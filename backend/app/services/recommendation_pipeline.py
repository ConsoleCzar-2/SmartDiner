"""Recommendation Pipeline Orchestrator — connects LLM, SQL Filter, ILP Solver, and Telemetry."""

import uuid
import json
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.constraints import ExtractedConstraints
from app.schemas.recommendation import (
    ChatRequest, ChatResponse, RecommendationResult, RecommendedItem
)
from app.services.intent_classifier import classify_intent
from app.services.constraint_extractor import extract_constraints
from app.services.constraint_merger import merge_constraints
from app.services.menu_filter import filter_menu_items
from app.services.optimizer import optimize_menu
from app.services.explanation_generator import (
    generate_explanation, generate_question_answer,
    stream_explanation, stream_question_answer
)
from app.services.restaurant_resolver import resolve_restaurant
from app.services.audit_logger import upload_audit_log_to_gcs
from app.models.restaurant import Restaurant
from app.models.conversation import Conversation


def sse_pack(event: str, data: dict) -> str:
    """Formats an event and JSON data into a Server-Sent Events text frame."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@dataclass
class RestaurantResolutionResult:
    """Carries outcome of restaurant resolution stage."""
    is_ambiguous: bool
    clarification_message: Optional[str] = None
    clarification_response: Optional[ChatResponse] = None
    active_restaurant_id: Optional[str] = None
    active_restaurant_name: Optional[str] = None
    cross_restaurant_meta: Optional[dict] = None
    existing_constraints: dict = None
    delta_constraints: Optional[ExtractedConstraints] = None


async def _load_conversation_state(
    request: ChatRequest, 
    db: AsyncSession
) -> tuple[Optional[Conversation], list, dict, Optional[str]]:
    """Loads existing conversation history, active constraints, and restaurant context."""
    conversation = None
    conversation_history = []
    existing_constraints = {}
    active_restaurant_id = str(request.restaurant_id) if request.restaurant_id else None

    if request.conversation_id:
        conversation = await db.get(Conversation, str(request.conversation_id))
        if conversation:
            conversation_history = conversation.messages or []
            existing_constraints = conversation.current_constraints or {}
            if not active_restaurant_id and conversation.restaurant_id:
                active_restaurant_id = str(conversation.restaurant_id)

    return conversation, conversation_history, existing_constraints, active_restaurant_id


async def _resolve_restaurant_context(
    request: ChatRequest,
    db: AsyncSession,
    user_id: str,
    conversation: Optional[Conversation],
    delta_constraints: ExtractedConstraints,
    active_restaurant_id: Optional[str],
    existing_constraints: dict
) -> RestaurantResolutionResult:
    """Resolves target restaurant, handles switching and ambiguous scenarios."""
    resolution = await resolve_restaurant(db, request.message, delta_constraints, current_restaurant_id=active_restaurant_id)
    active_restaurant_name = None
    cross_restaurant_meta = None

    if resolution["status"] in ("RESOLVED", "CROSS_RESTAURANT"):
        resolved_r = resolution["restaurant"]
        resolved_id = str(resolved_r.id)
        if active_restaurant_id and active_restaurant_id != resolved_id:
            active_restaurant_id = resolved_id
            active_restaurant_name = resolved_r.name
            if conversation:
                conversation.current_cart = []
                conversation.restaurant_id = active_restaurant_id
            general_keys = ["party_size", "vegetarians", "vegans", "non_vegetarians", "max_budget", "spice_level_preferred", "allergens"]
            existing_constraints = {k: v for k, v in existing_constraints.items() if k in general_keys and v is not None}
            if delta_constraints and hasattr(delta_constraints, "specific_dish_requests"):
                delta_constraints.specific_dish_requests = []
        elif not active_restaurant_id:
            active_restaurant_id = resolved_id
            active_restaurant_name = resolved_r.name
            if conversation:
                conversation.restaurant_id = active_restaurant_id
        else:
            active_restaurant_name = resolved_r.name

        if resolution["status"] == "CROSS_RESTAURANT":
            cross_restaurant_meta = {
                "status": resolution["status"],
                "is_cross_restaurant": True,
                "comparison_summary": resolution.get("comparison_summary"),
                "candidates": resolution.get("candidate_comparisons", [])
            }

        return RestaurantResolutionResult(
            is_ambiguous=False,
            active_restaurant_id=active_restaurant_id,
            active_restaurant_name=active_restaurant_name,
            cross_restaurant_meta=cross_restaurant_meta,
            existing_constraints=existing_constraints,
            delta_constraints=delta_constraints
        )

    # Ambiguous resolution
    if not active_restaurant_id:
        clarification_text = resolution.get("clarification_message", "Please select or name a restaurant to proceed.")
        if not conversation:
            conversation = Conversation(
                restaurant_id=None,
                user_id=user_id,
                messages=[],
                current_constraints={},
                current_cart=[]
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)

        new_msgs = list(conversation.messages or [])
        now_str = datetime.now(timezone.utc).isoformat()
        new_msgs.append({"id": str(uuid.uuid4()), "role": "user", "content": request.message, "createdAt": now_str})
        new_msgs.append({"id": str(uuid.uuid4()), "role": "assistant", "content": clarification_text, "createdAt": now_str})
        conversation.messages = new_msgs
        conversation.updated_at = datetime.now(timezone.utc)
        await db.commit()

        clarification_response = ChatResponse(
            conversation_id=UUID(conversation.id),
            restaurant_id=None,
            restaurant_name=None,
            recommendation=RecommendationResult(
                status="Infeasible",
                reason="Restaurant not resolved",
                items=[]
            ),
            explanation=clarification_text,
            extracted_constraints=delta_constraints,
            cross_restaurant_meta={"status": "AMBIGUOUS"}
        )

        return RestaurantResolutionResult(
            is_ambiguous=True,
            clarification_message=clarification_text,
            clarification_response=clarification_response,
            existing_constraints=existing_constraints,
            delta_constraints=delta_constraints
        )

    # Active restaurant already known but name needs lookup
    r_obj = await db.get(Restaurant, active_restaurant_id)
    if r_obj:
        active_restaurant_name = r_obj.name

    return RestaurantResolutionResult(
        is_ambiguous=False,
        active_restaurant_id=active_restaurant_id,
        active_restaurant_name=active_restaurant_name,
        cross_restaurant_meta=cross_restaurant_meta,
        existing_constraints=existing_constraints,
        delta_constraints=delta_constraints
    )


async def _ensure_conversation(
    db: AsyncSession,
    conversation: Optional[Conversation],
    user_id: str,
    active_restaurant_id: Optional[str]
) -> Conversation:
    """Ensures conversation entity exists and synchronizes active restaurant id."""
    if not conversation:
        conversation = Conversation(
            restaurant_id=active_restaurant_id,
            user_id=user_id,
            messages=[],
            current_constraints={},
            current_cart=[]
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
    elif active_restaurant_id and conversation.restaurant_id != active_restaurant_id:
        conversation.restaurant_id = active_restaurant_id
        conversation.updated_at = datetime.now(timezone.utc)
        await db.commit()
    return conversation


def _dispatch_gcs_audit(
    chat_response: ChatResponse,
    user_id: str,
    user_message: str,
    pipeline_telemetry: dict
) -> None:
    """Enqueues audit logging task to Google Cloud Storage asynchronously."""
    resolved_rest_id = str(chat_response.restaurant_id or "unassigned")
    try:
        recommended_cart = [
            item.model_dump() if hasattr(item, "model_dump") else item 
            for item in chat_response.recommendation.items
        ]
        asyncio.create_task(
            upload_audit_log_to_gcs(
                conversation_id=str(chat_response.conversation_id),
                user_id=str(user_id),
                restaurant_id=resolved_rest_id,
                user_message=user_message,
                extracted_constraints=chat_response.extracted_constraints.model_dump(),
                solver_output={
                    "status": chat_response.recommendation.status,
                    "total_cost": chat_response.recommendation.computed_total,
                    "total_servings": chat_response.recommendation.total_servings,
                    "decision_rationale": chat_response.recommendation.decision_rationale
                },
                llm_explanation=chat_response.explanation,
                recommended_cart=recommended_cart,
                intent=pipeline_telemetry.get("intent", {}),
                pipeline_telemetry=pipeline_telemetry
            )
        )
    except Exception:
        pass


async def _handle_non_recommendation_intent(
    request: ChatRequest,
    db: AsyncSession,
    user_id: str,
    conversation: Conversation,
    intent_result,
    existing_constraints: dict,
    conversation_history: list,
    active_restaurant_id: Optional[str],
    active_restaurant_name: Optional[str],
    cross_restaurant_meta: Optional[dict],
    enqueue_audit: bool,
    pipeline_telemetry: dict
) -> AsyncGenerator[dict, None]:
    """Handles short-circuit intents: QUESTION, GREETING, OFF_TOPIC, ADVERSARIAL."""
    now_str = datetime.now(timezone.utc).isoformat()

    if intent_result.intent == "QUESTION":
        yield {
            "event": "status", 
            "data": {"step": "answering", "message": "Answering question about your order..."}
        }
        full_answer = ""
        async for ev in stream_question_answer(
            request.message,
            conversation.current_cart or [],
            existing_constraints,
            conversation_history
        ):
            if ev["type"] == "token":
                full_answer += ev["content"]
                yield {"event": "token", "data": {"content": ev["content"]}}
            elif ev["type"] == "done":
                pipeline_telemetry["llm_calls"].append(ev["telemetry"])

        new_messages = list(conversation.messages or [])
        new_messages.append({"id": str(uuid.uuid4()), "role": "user", "content": request.message, "createdAt": now_str})
        new_messages.append({"id": str(uuid.uuid4()), "role": "assistant", "content": full_answer, "createdAt": now_str})
        conversation.messages = new_messages
        conversation.updated_at = datetime.now(timezone.utc)
        await db.commit()

        computed_total = sum(item.get("subtotal", 0) for item in (conversation.current_cart or []))
        budget_remaining = None
        if existing_constraints.get("max_budget"):
            budget_remaining = round(existing_constraints["max_budget"] - computed_total, 2)

        rec = RecommendationResult(
            status="Optimal",
            reason="Restored from draft",
            items=conversation.current_cart or [],
            computed_total=computed_total,
            budget_remaining=budget_remaining,
            total_servings=0,
            veg_servings=0,
            vegan_servings=0,
            nonveg_servings=0,
            decision_rationale=None
        )

        chat_res = ChatResponse(
            conversation_id=UUID(conversation.id),
            restaurant_id=UUID(active_restaurant_id) if active_restaurant_id else None,
            restaurant_name=active_restaurant_name,
            recommendation=rec,
            explanation=full_answer,
            extracted_constraints=ExtractedConstraints(**existing_constraints) if existing_constraints else ExtractedConstraints(),
            cross_restaurant_meta=cross_restaurant_meta
        )

        if enqueue_audit:
            _dispatch_gcs_audit(chat_res, user_id, request.message, pipeline_telemetry)

        yield {"event": "done", "response": chat_res, "telemetry": pipeline_telemetry}
        return

    # Non-question rejection/greeting
    if intent_result.intent == "GREETING":
        rejection_message = "Hello! Welcome to SmartDiner Concierge. Tell me about your party size, budget, or preferred dishes, and I'll find or design the perfect meal for you."
    else:
        rejection_message = "I can help you with finding dishes across restaurants, ordering food, modifying your cart, or answering menu questions."

    yield {"event": "token", "data": {"content": rejection_message}}

    new_messages = list(conversation.messages or [])
    new_messages.append({"id": str(uuid.uuid4()), "role": "user", "content": request.message, "createdAt": now_str})
    new_messages.append({"id": str(uuid.uuid4()), "role": "assistant", "content": rejection_message, "createdAt": now_str})
    conversation.messages = new_messages
    conversation.updated_at = datetime.now(timezone.utc)
    await db.commit()

    chat_res = ChatResponse(
        conversation_id=UUID(conversation.id),
        restaurant_id=UUID(active_restaurant_id) if active_restaurant_id else None,
        restaurant_name=active_restaurant_name,
        recommendation=RecommendationResult(
            status="Infeasible",
            reason=intent_result.reason,
            items=[]
        ),
        explanation=rejection_message,
        extracted_constraints=ExtractedConstraints(),
        cross_restaurant_meta=cross_restaurant_meta
    )

    if enqueue_audit:
        _dispatch_gcs_audit(chat_res, user_id, request.message, pipeline_telemetry)

    yield {"event": "done", "response": chat_res, "telemetry": pipeline_telemetry}


def _build_recommendation_result(
    solver_output: dict, 
    constraints: ExtractedConstraints
) -> tuple[RecommendationResult, list[RecommendedItem]]:
    """Converts ILP solver output into typed RecommendedItems and computes breakdown metrics."""
    recommended_items = []
    veg_servings = 0
    vegan_servings = 0
    nonveg_servings = 0

    for entry in solver_output.get("items", []):
        item = entry["item"]
        item_servings = entry["quantity"] * item.serving_size
        if item.dietary_preference == "Vegetarian":
            veg_servings += item_servings
        elif item.dietary_preference == "Vegan":
            vegan_servings += item_servings
        else:
            nonveg_servings += item_servings

        recommended_items.append(RecommendedItem(
            id=str(item.id),
            name=item.name,
            category=item.category,
            quantity=entry["quantity"],
            unit_price=float(item.price),
            subtotal=entry["subtotal"],
            dietary_preference=item.dietary_preference,
            spice_level=item.spice_level,
            serving_size=item.serving_size,
            total_servings=item_servings,
            image_url=item.image_url,
        ))

    budget_remaining = None
    if constraints.max_budget:
        budget_remaining = round(constraints.max_budget - solver_output["total_cost"], 2)

    recommendation = RecommendationResult(
        status=solver_output["status"],
        reason=solver_output.get("reason", ""),
        items=recommended_items,
        computed_total=solver_output["total_cost"],
        budget_remaining=budget_remaining,
        total_servings=solver_output["total_servings"],
        veg_servings=veg_servings,
        vegan_servings=vegan_servings,
        nonveg_servings=nonveg_servings,
        decision_rationale=solver_output.get("decision_rationale", None)
    )

    return recommendation, recommended_items


async def _save_conversation_state(
    db: AsyncSession,
    conversation: Conversation,
    user_message: str,
    assistant_message: str,
    constraints: ExtractedConstraints,
    recommended_items: list[RecommendedItem],
    active_restaurant_id: Optional[str]
) -> None:
    """Persists conversational state, updated cart, and merged constraints to database."""
    now_str = datetime.now(timezone.utc).isoformat()
    new_messages = list(conversation.messages or [])
    new_messages.append({"id": str(uuid.uuid4()), "role": "user", "content": user_message, "createdAt": now_str})
    new_messages.append({"id": str(uuid.uuid4()), "role": "assistant", "content": assistant_message, "createdAt": now_str})

    conversation.messages = new_messages
    conversation.current_constraints = constraints.model_dump()
    conversation.current_cart = [item.model_dump() for item in recommended_items]
    if active_restaurant_id:
        conversation.restaurant_id = active_restaurant_id
    conversation.updated_at = datetime.now(timezone.utc)
    await db.commit()


async def _execute_recommendation_pipeline(
    request: ChatRequest, 
    db: AsyncSession, 
    user_id: str, 
    enqueue_audit: bool = True
) -> AsyncGenerator[dict, None]:
    """
    Canonical recommendation pipeline engine.
    Yields internal event dictionaries:
      - {"event": "status", "data": {"step": ..., "message": ...}}
      - {"event": "cart", "data": {"recommendation": ...}}
      - {"event": "token", "data": {"content": ...}}
      - {"event": "done", "response": ChatResponse, "telemetry": dict}
    """
    pipeline_telemetry = {
        "intent": {},
        "llm_calls": [],
        "sql_queries": [],
        "cache_hits": [],
        "solver_decision": {}
    }

    yield {
        "event": "status",
        "data": {"step": "intent_and_constraints", "message": "Analyzing dietary requirements and budget constraints..."}
    }

    # Step 0: Conversation State Management
    conversation, conversation_history, existing_constraints, active_restaurant_id = await _load_conversation_state(request, db)

    # Step 0.5 & 1: Parallel Intent Classification & Constraint Extraction
    (intent_result, intent_meta), (delta_constraints, extractor_meta) = await asyncio.gather(
        classify_intent(request.message),
        extract_constraints(
            request.message, 
            conversation_history=conversation_history, 
            existing_constraints=existing_constraints,
            current_cart=conversation.current_cart if conversation else None
        )
    )
    pipeline_telemetry["intent"] = intent_result.model_dump()
    pipeline_telemetry["llm_calls"].extend([intent_meta, extractor_meta])

    yield {
        "event": "status",
        "data": {"step": "resolving_restaurant", "message": "Resolving restaurant selection..."}
    }

    # Step 0.8: Resolve Restaurant
    rest_ctx = await _resolve_restaurant_context(
        request, db, user_id, conversation, delta_constraints, active_restaurant_id, existing_constraints
    )
    if rest_ctx.is_ambiguous:
        yield {"event": "token", "data": {"content": rest_ctx.clarification_message}}
        yield {"event": "done", "response": rest_ctx.clarification_response, "telemetry": pipeline_telemetry}
        return

    active_restaurant_id = rest_ctx.active_restaurant_id
    active_restaurant_name = rest_ctx.active_restaurant_name
    cross_restaurant_meta = rest_ctx.cross_restaurant_meta
    existing_constraints = rest_ctx.existing_constraints
    delta_constraints = rest_ctx.delta_constraints

    conversation = await _ensure_conversation(db, conversation, user_id, active_restaurant_id)

    # Step 1: Handle Non-Recommendation Intents
    if intent_result.intent in ["OFF_TOPIC", "ADVERSARIAL", "GREETING", "QUESTION"]:
        async for ev in _handle_non_recommendation_intent(
            request, db, user_id, conversation, intent_result, existing_constraints,
            conversation_history, active_restaurant_id, active_restaurant_name,
            cross_restaurant_meta, enqueue_audit, pipeline_telemetry
        ):
            yield ev
        return

    # Step 1.5: Deterministic State Merging
    constraints = merge_constraints(existing_constraints, delta_constraints)

    yield {
        "event": "status",
        "data": {"step": "filtering_menu", "message": "Filtering menu items by allergens, dietary preferences, and availability..."}
    }

    # Step 2: SQL Deterministic Filter
    filtered, query_meta = await filter_menu_items(db, active_restaurant_id, constraints)
    pipeline_telemetry["sql_queries"].append(query_meta)
    if "cache_event" in query_meta:
        pipeline_telemetry["cache_hits"].append(query_meta["cache_event"])
    safety_notes = query_meta.get("safety_notes", [])

    yield {
        "event": "status",
        "data": {"step": "optimizing_meal", "message": "Optimizing meal combination and budget using ILP solver..."}
    }

    # Step 3: ILP Optimization
    solver_output = optimize_menu(filtered["veg"], filtered["vegan"], filtered["nonveg"], constraints)
    if safety_notes:
        if "decision_rationale" not in solver_output or not solver_output["decision_rationale"]:
            solver_output["decision_rationale"] = {}
        solver_output["decision_rationale"]["safety_notes"] = safety_notes
    pipeline_telemetry["solver_decision"] = solver_output.get("decision_rationale", {})

    # Step 4: Build structured recommendation result
    recommendation, recommended_items = _build_recommendation_result(solver_output, constraints)
    yield {"event": "cart", "data": {"recommendation": recommendation.model_dump()}}

    yield {
        "event": "status",
        "data": {"step": "generating_explanation", "message": "Generating grounded explanation..."}
    }

    # Step 5: Grounded LLM Explanation Streaming
    full_explanation = ""
    if cross_restaurant_meta and cross_restaurant_meta.get("comparison_summary"):
        prefix = f"{cross_restaurant_meta['comparison_summary']}\n\n"
        full_explanation += prefix
        yield {"event": "token", "data": {"content": prefix}}

    async for ev in stream_explanation(solver_output, constraints, safety_notes=safety_notes):
        if ev["type"] == "token":
            full_explanation += ev["content"]
            yield {"event": "token", "data": {"content": ev["content"]}}
        elif ev["type"] == "done":
            pipeline_telemetry["llm_calls"].append(ev["telemetry"])

    # Step 6: Save State
    await _save_conversation_state(
        db, conversation, request.message, full_explanation, constraints, recommended_items, active_restaurant_id
    )

    chat_response = ChatResponse(
        conversation_id=UUID(conversation.id),
        restaurant_id=UUID(active_restaurant_id) if active_restaurant_id else None,
        restaurant_name=active_restaurant_name,
        recommendation=recommendation,
        explanation=full_explanation,
        extracted_constraints=constraints,
        cross_restaurant_meta=cross_restaurant_meta
    )

    if enqueue_audit:
        _dispatch_gcs_audit(chat_response, user_id, request.message, pipeline_telemetry)

    yield {
        "event": "done",
        "response": chat_response,
        "telemetry": pipeline_telemetry
    }


async def stream_chat_pipeline(request: ChatRequest, db: AsyncSession, user_id: str):
    """
    Streaming recommendation pipeline via Server-Sent Events (SSE).
    Yields event frames formatted for text/event-stream.
    """
    async for item in _execute_recommendation_pipeline(request, db, user_id, enqueue_audit=True):
        if item["event"] == "done":
            yield sse_pack("done", {
                "response": item["response"].model_dump(mode="json"),
                "telemetry": item["telemetry"]
            })
        else:
            yield sse_pack(item["event"], item["data"])


async def process_chat_request(request: ChatRequest, db: AsyncSession, user_id: str) -> tuple[ChatResponse, dict]:
    """
    Unary recommendation pipeline adapter.
    Drains the canonical generator to produce a single (ChatResponse, pipeline_telemetry) tuple.
    """
    chat_response = None
    telemetry = None
    async for item in _execute_recommendation_pipeline(request, db, user_id, enqueue_audit=False):
        if item["event"] == "done":
            chat_response = item["response"]
            telemetry = item["telemetry"]

    if not chat_response:
        raise RuntimeError("Recommendation pipeline completed unexpectedly without a response.")

    return chat_response, telemetry
