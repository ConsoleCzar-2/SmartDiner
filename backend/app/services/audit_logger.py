import json
import logging
import asyncio
from datetime import datetime, timezone
from google.cloud import storage
from app.config import settings
from app.services.gcs_client import get_storage_client

logger = logging.getLogger(__name__)

async def upload_audit_log_to_gcs(
    conversation_id: str,
    user_id: str,
    restaurant_id: str,
    user_message: str,
    extracted_constraints: dict,
    solver_output: dict,
    llm_explanation: str,
    recommended_cart: list,
    intent: dict = None,
    pipeline_telemetry: dict = None
):
    """
    Asynchronously uploads an enriched WORM audit log to GCS containing the full context
    and telemetry (SQL queries, cache hits, token usage, solver decisions) of the recommendation.
    Runs inside a FastAPI BackgroundTask so it doesn't block the HTTP response.
    """
    if not settings.gcs_audit_bucket_name:
        logger.warning("GCS_AUDIT_BUCKET_NAME is not set. Skipping audit logging.")
        return

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "conversation_id": conversation_id,
        "user_id": user_id,
        "restaurant_id": restaurant_id,
        "user_message": user_message,
        "intent": intent or {},
        "extracted_constraints": extracted_constraints,
        "pipeline_telemetry": pipeline_telemetry or {},
        "solver_output": solver_output,
        "llm_explanation": llm_explanation,
        "recommended_cart": recommended_cart
    }

    def _sync_upload():
        try:
            client = get_storage_client()
            bucket = client.bucket(settings.gcs_audit_bucket_name)
            
            # Create a unique blob name using the conversation_id and a timestamp
            blob_name = f"audit_logs/{conversation_id}/{payload['timestamp'].replace(':', '-')}.json"
            blob = bucket.blob(blob_name)
            
            # Upload the JSON payload
            blob.upload_from_string(
                data=json.dumps(payload, indent=2, default=str),
                content_type="application/json"
            )
            
            logger.info(f"Successfully uploaded WORM audit log to gs://{settings.gcs_audit_bucket_name}/{blob_name}")
            try:
                from app.services.admin_insights import invalidate_gcs_metrics_cache
                invalidate_gcs_metrics_cache()
            except Exception:
                pass
        except Exception as e:
            logger.error("Failed to upload audit log to GCS: %s", e)

    # Run the synchronous google-cloud-storage library in an executor to avoid blocking the async event loop
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _sync_upload)
