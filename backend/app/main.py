"""SmartDiner FastAPI Application Entry Point"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
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
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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


# Import and include routers here when created
# from app.routers import menu, orders, recommendations
# app.include_router(menu.router, prefix="/api/v1/menu", tags=["menu"])
# app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
# app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["recommendations"])