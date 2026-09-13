import json
import logging
import time
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from google import genai
from google.cloud import storage

from app.config import settings
from app.services.gcs_client import get_storage_client
from app.models.admin_user import AdminUser
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem
from app.models.order import Order, OrderItem
from app.models.conversation import Conversation
from app.prompts.admin_insights_prompt import ADMIN_INSIGHTS_SYSTEM_PROMPT, ADMIN_CLASSIFIER_PROMPT

logger = logging.getLogger(__name__)


async def classify_admin_query(message: str) -> str:
    """
    Classifies admin query into 'POSTGRES', 'GCS', or 'BOTH'.
    """
    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = await client.aio.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=f"Admin Query: {message}",
            config={
                "system_instruction": ADMIN_CLASSIFIER_PROMPT,
                "response_mime_type": "application/json",
                "temperature": 0.0
            }
        )
        data = json.loads(response.text)
        src = data.get("source", "POSTGRES").upper()
        if src in ("POSTGRES", "GCS", "BOTH"):
            return src
        return "POSTGRES"
    except Exception as e:
        logger.warning(f"Failed to classify admin query via LLM: {e}. Defaulting to BOTH.")
        # Keyword fallback
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["token", "latency", "cost", "telemetry", "gcs", "audit", "solver", "infeasible", "feasible", "allergen"]):
            if any(w in msg_lower for w in ["order", "revenue", "sale", "dish", "customer", "conversation", "restaurant"]):
                return "BOTH"
            return "GCS"
        if any(w in msg_lower for w in ["conversation", "query", "queries", "session"]):
            return "POSTGRES"
        return "POSTGRES"


async def fetch_postgres_metrics(db: AsyncSession, admin_user: AdminUser) -> dict:
    """
    Aggregates business metrics from PostgreSQL with strict RBAC.
    """
    rest_filter = None
    is_scoped = admin_user.role == "RESTAURANT_ADMIN" and admin_user.restaurant_id
    if is_scoped:
        rest_filter = admin_user.restaurant_id

    metrics = {
        "admin_role": admin_user.role,
        "restaurant_scope": str(rest_filter) if rest_filter else "ALL_RESTAURANTS",
        "platform_currency": "INR (₹)"
    }

    # 1. Total Restaurants
    rest_q = select(Restaurant)
    if is_scoped:
        rest_q = rest_q.where(Restaurant.id == rest_filter)
    rest_res = await db.execute(rest_q)
    restaurants = rest_res.scalars().all()
    metrics["restaurants"] = [{"id": str(r.id), "name": r.name, "cuisine": r.cuisine_type} for r in restaurants]

    # 2. Total Orders & Revenue (Formatted in INR)
    order_q = select(
        func.count(Order.id).label("total_orders"),
        func.coalesce(func.sum(Order.total_amount), 0).label("total_revenue"),
        func.coalesce(func.avg(Order.total_amount), 0).label("avg_order_value")
    )
    if is_scoped:
        order_q = order_q.where(Order.restaurant_id == rest_filter)
    order_res = await db.execute(order_q)
    ord_row = order_res.first()
    tot_rev = float(ord_row.total_revenue) if ord_row else 0.0
    avg_val = round(float(ord_row.avg_order_value), 2) if ord_row else 0.0
    metrics["orders_summary"] = {
        "currency": "INR (₹)",
        "total_orders": ord_row.total_orders if ord_row else 0,
        "total_revenue": f"₹{tot_rev:,.2f}",
        "avg_order_value": f"₹{avg_val:,.2f}",
        "raw_total_revenue_inr": tot_rev,
        "raw_avg_order_value_inr": avg_val
    }

    # 3. Top Dishes by Order Volume
    top_dishes_q = (
        select(
            MenuItem.name,
            MenuItem.category,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("qty_sold"),
            func.coalesce(func.sum(OrderItem.subtotal), 0).label("revenue_generated")
        )
        .join(MenuItem, OrderItem.menu_item_id == MenuItem.id)
    )
    if is_scoped:
        top_dishes_q = top_dishes_q.where(MenuItem.restaurant_id == rest_filter)
    top_dishes_q = top_dishes_q.group_by(MenuItem.id, MenuItem.name, MenuItem.category).order_by(desc("qty_sold")).limit(10)
    top_dishes_res = await db.execute(top_dishes_q)
    metrics["top_selling_dishes"] = [
        {
            "name": row.name, 
            "category": row.category, 
            "quantity_sold": row.qty_sold, 
            "revenue": f"₹{float(row.revenue_generated):,.2f}"
        }
        for row in top_dishes_res.all()
    ]

    # 4. Menu Composition
    menu_q = select(
        MenuItem.category,
        func.count(MenuItem.id).label("count"),
        func.avg(MenuItem.price).label("avg_price")
    )
    if is_scoped:
        menu_q = menu_q.where(MenuItem.restaurant_id == rest_filter)
    menu_q = menu_q.group_by(MenuItem.category)
    menu_res = await db.execute(menu_q)
    metrics["menu_categories"] = [
        {
            "category": row.category, 
            "item_count": row.count, 
            "avg_price": f"₹{round(float(row.avg_price), 2):,.2f}"
        }
        for row in menu_res.all()
    ]

    # 5. Conversations Volume & Recent Conversation History
    conv_q = select(func.count(Conversation.id).label("total_conversations"))
    if is_scoped:
        conv_q = conv_q.where(Conversation.restaurant_id == rest_filter)
    conv_res = await db.execute(conv_q)
    c_row = conv_res.first()
    metrics["total_conversations"] = c_row.total_conversations if c_row else 0

    recent_conv_q = (
        select(Conversation, Restaurant.name.label("restaurant_name"))
        .outerjoin(Restaurant, Conversation.restaurant_id == Restaurant.id)
        .order_by(desc(Conversation.updated_at))
        .limit(10)
    )
    if is_scoped:
        recent_conv_q = recent_conv_q.where(Conversation.restaurant_id == rest_filter)

    recent_conv_res = await db.execute(recent_conv_q)
    recent_convs = []
    for c, r_name in recent_conv_res.all():
        first_user_msg = ""
        last_user_msg = ""
        if c.messages and isinstance(c.messages, list):
            for m in c.messages:
                if m.get("role") == "user":
                    if not first_user_msg:
                        first_user_msg = m.get("content", "")
                    last_user_msg = m.get("content", "")

        recent_convs.append({
            "conversation_id": str(c.id),
            "restaurant_selected": r_name or "Global Concierge / Cross-Restaurant",
            "status": c.status,
            "first_user_query": first_user_msg[:160] if first_user_msg else "N/A",
            "latest_user_query": last_user_msg[:160] if last_user_msg else "N/A",
            "constraints": c.current_constraints if c.current_constraints else {},
            "items_in_cart_count": len(c.current_cart) if c.current_cart and isinstance(c.current_cart, list) else 0,
            "updated_at": c.updated_at.strftime("%Y-%m-%d %H:%M") if c.updated_at else None
        })
    metrics["recent_conversations"] = recent_convs

    return metrics


from concurrent.futures import ThreadPoolExecutor

_GCS_METRICS_CACHE: dict = {}
_GCS_METRICS_CACHE_TIME: dict = {}
_GCS_CACHE_TTL: float = 120.0  # 2-minute in-memory cache


def fetch_gcs_audit_metrics(admin_user: AdminUser) -> dict:
    """
    Reads recent GCS audit logs and computes telemetry aggregates.
    Uses concurrent blob downloading and 120-second in-memory caching.
    """
    if not settings.gcs_audit_bucket_name:
        return {
            "status": "UNCONFIGURED",
            "message": "GCS_AUDIT_BUCKET_NAME is not set. In local development without GCS bucket, token logs are simulated.",
            "total_audit_records": 0,
            "total_tokens_used": 0,
            "avg_latency_ms": 0
        }

    is_scoped = admin_user.role == "RESTAURANT_ADMIN" and admin_user.restaurant_id
    scoped_rest_id = str(admin_user.restaurant_id) if is_scoped else None
    cache_key = f"{admin_user.role}_{scoped_rest_id or 'ALL'}"

    # Return cached data if fresh
    now = time.time()
    if cache_key in _GCS_METRICS_CACHE and (now - _GCS_METRICS_CACHE_TIME.get(cache_key, 0)) < _GCS_CACHE_TTL:
        return _GCS_METRICS_CACHE[cache_key]

    try:
        client = get_storage_client()
        bucket = client.bucket(settings.gcs_audit_bucket_name)
        
        # Read latest 20 blobs
        blobs = list(bucket.list_blobs(prefix="audit_logs/", max_results=20))
        if not blobs:
            res = {"status": "EMPTY", "message": "No audit logs found in bucket.", "records_count": 0}
            _GCS_METRICS_CACHE[cache_key] = res
            _GCS_METRICS_CACHE_TIME[cache_key] = now
            return res

        def _download_blob(b):
            try:
                return json.loads(b.download_as_bytes())
            except Exception as parse_err:
                logger.debug(f"Error parsing blob {b.name}: {parse_err}")
                return None

        # Download blobs concurrently using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=8) as executor:
            parsed_blobs = list(executor.map(_download_blob, blobs))

        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0
        latencies = []
        solver_optimal = 0
        solver_infeasible = 0
        records_counted = 0
        step_tokens = {}
        allergen_exclusions_detected = {}
        recent_audit_queries = []
        total_cache_lookups = 0
        total_cache_hits = 0
        total_cache_misses = 0
        cache_latencies = []

        for content in parsed_blobs:
            if not content:
                continue

            try:
                # Enforce RBAC
                if scoped_rest_id and str(content.get("restaurant_id")) != scoped_rest_id:
                    continue

                records_counted += 1
                telemetry = content.get("pipeline_telemetry", {})
                
                # Check allergen exclusions in extracted_constraints or sql filters
                extracted_c = content.get("extracted_constraints", {})
                allergens = extracted_c.get("excluded_allergens", [])
                if allergens and isinstance(allergens, list):
                    for a in allergens:
                        allergen_exclusions_detected[a] = allergen_exclusions_detected.get(a, 0) + 1

                for sq in telemetry.get("sql_queries", []):
                    for sn in sq.get("safety_notes", []):
                        allergen_exclusions_detected[sn] = allergen_exclusions_detected.get(sn, 0) + 1

                # Sample recent queries
                user_msg = content.get("user_message")
                solver_stat = content.get("solver_output", {}).get("status")
                if user_msg and len(recent_audit_queries) < 10:
                    recent_audit_queries.append({
                        "user_message": user_msg[:140],
                        "solver_status": solver_stat or "Unknown",
                        "restaurant_id": content.get("restaurant_id"),
                        "timestamp": content.get("timestamp")
                    })

                # LLM calls telemetry
                for call in telemetry.get("llm_calls", []):
                    p_tok = call.get("prompt_tokens", 0)
                    c_tok = call.get("completion_tokens", 0)
                    tot = call.get("total_tokens", 0) or (p_tok + c_tok)
                    total_prompt_tokens += p_tok
                    total_completion_tokens += c_tok
                    total_tokens += tot
                    step_name = call.get("step", "unknown")
                    step_tokens[step_name] = step_tokens.get(step_name, 0) + tot
                    if "latency_ms" in call:
                        latencies.append(call["latency_ms"])

                # Cache hits telemetry
                for ch in telemetry.get("cache_hits", []):
                    total_cache_lookups += 1
                    if ch.get("status") == "HIT" or ch.get("hit") is True:
                        total_cache_hits += 1
                    else:
                        total_cache_misses += 1
                    if "duration_ms" in ch:
                        cache_latencies.append(ch["duration_ms"])

                # Solver status
                if solver_stat == "Optimal":
                    solver_optimal += 1
                elif solver_stat == "Infeasible":
                    solver_infeasible += 1
            except Exception as parse_err:
                logger.debug(f"Error parsing audit content: {parse_err}")
                continue

        avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
        avg_cache_lat = round(sum(cache_latencies) / len(cache_latencies), 3) if cache_latencies else 0.0

        res = {
            "status": "SUCCESS",
            "audit_records_analyzed": records_counted,
            "total_tokens_consumed": total_tokens,
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "token_breakdown_by_step": step_tokens,
            "average_llm_latency_ms": avg_lat,
            "solver_decisions": {
                "optimal_count": solver_optimal,
                "infeasible_count": solver_infeasible,
                "feasibility_rate_pct": round((solver_optimal / (solver_optimal + solver_infeasible) * 100), 1) if (solver_optimal + solver_infeasible) > 0 else 100.0
            },
            "cache_telemetry": {
                "total_lookups": total_cache_lookups,
                "hits": total_cache_hits,
                "misses": total_cache_misses,
                "hit_rate_pct": round((total_cache_hits / total_cache_lookups * 100), 1) if total_cache_lookups > 0 else 0.0,
                "average_cache_latency_ms": avg_cache_lat
            },
            "allergen_exclusions": {
                "total_allergen_events_recorded": sum(allergen_exclusions_detected.values()),
                "breakdown_by_allergen": allergen_exclusions_detected
            },
            "recent_audit_queries": recent_audit_queries
        }
        _GCS_METRICS_CACHE[cache_key] = res
        _GCS_METRICS_CACHE_TIME[cache_key] = now
        return res
    except Exception as e:
        logger.error(f"GCS audit retrieval error: {e}")
        if cache_key in _GCS_METRICS_CACHE:
            return _GCS_METRICS_CACHE[cache_key]
        return {
            "status": "ERROR",
            "error_detail": str(e),
            "message": "Failed to connect to GCS bucket for audit metrics."
        }


async def generate_admin_insight(
    db: AsyncSession,
    admin_user: AdminUser,
    message: str
) -> dict:
    """
    End-to-end admin insight generator:
      1. Classify prompt into POSTGRES, GCS, or BOTH
      2. Retrieve scoped data from required source(s)
      3. Construct grounded DATA_CONTEXT
      4. Synthesize executive analysis using Gemini 3.5 Flash Lite
    """
    target_source = await classify_admin_query(message)
    
    postgres_data = None
    gcs_data = None
    sources_used = []

    if target_source in ("POSTGRES", "BOTH"):
        postgres_data = await fetch_postgres_metrics(db, admin_user)
        sources_used.append("PostgreSQL Database")

    if target_source in ("GCS", "BOTH"):
        gcs_data = fetch_gcs_audit_metrics(admin_user)
        sources_used.append("GCS WORM Audit Logs")

    # Build context string
    context_sections = []
    if postgres_data:
        context_sections.append(f"=== POSTGRESQL BUSINESS & OPERATIONAL DATA ===\n{json.dumps(postgres_data, indent=2)}")
    if gcs_data:
        context_sections.append(f"=== GCS WORM AUDIT & TELEMETRY LOGS ===\n{json.dumps(gcs_data, indent=2)}")

    full_context = "\n\n".join(context_sections)

    prompt = (
        f"DATA_CONTEXT:\n"
        f"{full_context}\n\n"
        f"ADMIN USER QUESTION: {message}\n\n"
        f"Provide a structured, executive answer strictly grounded in the DATA_CONTEXT above."
    )

    client = genai.Client(api_key=settings.gemini_api_key)
    response = await client.aio.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config={
            "system_instruction": ADMIN_INSIGHTS_SYSTEM_PROMPT,
            "temperature": 0.2
        }
    )

    return {
        "answer": response.text,
        "target_source": target_source,
        "data_sources": sources_used,
        "metrics_summary": {
            "orders": postgres_data.get("orders_summary") if postgres_data else None,
            "gcs_records": gcs_data.get("audit_records_analyzed") if gcs_data else None,
            "total_tokens": gcs_data.get("total_tokens_consumed") if gcs_data else None
        }
    }


def sse_admin_pack(event: str, data: dict) -> str:
    """Formats an event and JSON data into a Server-Sent Events text frame."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_admin_insight(
    db: AsyncSession,
    admin_user: AdminUser,
    message: str
):
    """
    Streaming administrative business intelligence via Server-Sent Events.
    Yields:
      - 'status': intermediate notifications ('classifying', 'retrieving', 'synthesizing')
      - 'metadata': resolved data sources and metric summaries
      - 'token': streaming insight text tokens
      - 'done': full response payload
    """
    yield sse_admin_pack("status", {
        "step": "classifying",
        "message": "Classifying query intent and target data source..."
    })

    target_source = await classify_admin_query(message)

    yield sse_admin_pack("status", {
        "step": "retrieving",
        "message": f"Querying {target_source} data sources with role-based access control..."
    })

    postgres_data = None
    gcs_data = None
    sources_used = []

    if target_source in ("POSTGRES", "BOTH"):
        postgres_data = await fetch_postgres_metrics(db, admin_user)
        sources_used.append("PostgreSQL Database")

    if target_source in ("GCS", "BOTH"):
        gcs_data = await asyncio.to_thread(fetch_gcs_audit_metrics, admin_user)
        sources_used.append("GCS WORM Audit Logs")

    metrics_summary = {
        "orders": postgres_data.get("orders_summary") if postgres_data else None,
        "gcs_records": gcs_data.get("audit_records_analyzed") if gcs_data else None,
        "total_tokens": gcs_data.get("total_tokens_consumed") if gcs_data else None
    }

    yield sse_admin_pack("metadata", {
        "target_source": target_source,
        "data_sources": sources_used,
        "metrics_summary": metrics_summary
    })

    yield sse_admin_pack("status", {
        "step": "synthesizing",
        "message": "Synthesizing executive insight with Gemini 3.5 Flash Lite..."
    })

    context_sections = []
    if postgres_data:
        context_sections.append(f"=== POSTGRESQL BUSINESS & OPERATIONAL DATA ===\n{json.dumps(postgres_data, indent=2)}")
    if gcs_data:
        context_sections.append(f"=== GCS WORM AUDIT & TELEMETRY LOGS ===\n{json.dumps(gcs_data, indent=2)}")

    full_context = "\n\n".join(context_sections)

    prompt = (
        f"DATA_CONTEXT:\n"
        f"{full_context}\n\n"
        f"ADMIN USER QUESTION: {message}\n\n"
        f"Provide a structured, executive answer strictly grounded in the DATA_CONTEXT above."
    )

    client = genai.Client(api_key=settings.gemini_api_key)
    response_stream = await client.aio.models.generate_content_stream(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config={
            "system_instruction": ADMIN_INSIGHTS_SYSTEM_PROMPT,
            "temperature": 0.2
        }
    )

    full_text = []
    async for chunk in response_stream:
        text = chunk.text or ""
        if text:
            full_text.append(text)
            yield sse_admin_pack("token", {"content": text})

    yield sse_admin_pack("done", {
        "answer": "".join(full_text),
        "target_source": target_source,
        "data_sources": sources_used,
        "metrics_summary": metrics_summary
    })

