"""SmartDiner FastAPI Application Entry Point"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db


import os, json, tempfile

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # If running on Render (or anywhere without ADC), bootstrap GCS credentials from env
    creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if creds_json and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        creds_path = os.path.join(tempfile.gettempdir(), "gcs-credentials.json")
        with open(creds_path, "w") as f:
            f.write(creds_json)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description="AI-powered restaurant assistant with allergen safety, budget compliance, and dietary adherence",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
    swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"}
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Welcome to SmartDiner API",
        "version": "0.1.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "smartdiner-backend",
        "environment": settings.app_env
    }


# Import and include routers
from app.routers import chat, menu, admin, auth, orders, cart, admin_menu
app.include_router(chat.router)
app.include_router(menu.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(cart.router)
app.include_router(admin_menu.router)
# reload
