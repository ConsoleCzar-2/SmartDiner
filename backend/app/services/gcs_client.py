import os
import json
import logging
from typing import Optional
from google.cloud import storage
from google.oauth2 import service_account
from app.config import settings

logger = logging.getLogger(__name__)

def get_storage_client() -> storage.Client:
    """
    Returns an authenticated google.cloud.storage.Client.
    Automatically resolves credentials in order:
    1. GOOGLE_APPLICATION_CREDENTIALS environment variable (if pointing to a valid file)
    2. Render Secret File mounted at /etc/secrets/gcp-credentials.json
    3. Root or local repository gcp-credentials.json
    4. GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable containing raw JSON string
    5. Fallback to default Application Default Credentials (ADC)
    """
    # 1. Check if GOOGLE_APPLICATION_CREDENTIALS is set and points to an existing file
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and os.path.isfile(creds_path):
        try:
            return storage.Client.from_service_account_json(
                creds_path,
                project=settings.gcp_project_id or None
            )
        except Exception as e:
            logger.warning("Failed to initialize storage client from GOOGLE_APPLICATION_CREDENTIALS: %s", e)

    # 2. Check standard candidate locations (e.g. Render Secret Files)
    candidates = [
        "/etc/secrets/gcp-credentials.json",  # Render standard secret file mount path
        "gcp-credentials.json",
        "../gcp-credentials.json",
        os.path.join(os.getcwd(), "gcp-credentials.json"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gcp-credentials.json"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "gcp-credentials.json"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(path)
                return storage.Client.from_service_account_json(
                    path,
                    project=settings.gcp_project_id or None
                )
            except Exception as e:
                logger.warning("Found credentials at %s but failed to load: %s", path, e)

    # 3. Check if raw JSON was passed in env var
    creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if creds_json:
        try:
            info = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(info)
            return storage.Client(
                credentials=credentials,
                project=settings.gcp_project_id or info.get("project_id") or None
            )
        except Exception as e:
            logger.warning("Failed to parse GOOGLE_APPLICATION_CREDENTIALS_JSON: %s", e)

    # 4. Fallback to default ADC
    return storage.Client(project=settings.gcp_project_id or None)
