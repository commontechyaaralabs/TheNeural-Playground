from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging
import asyncio
import threading
import os

from .config import settings
from .api import projects, health, teachers, students, classrooms, demo_projects, scratch_services
from .api.guests import router as guests_router
from .training_worker import training_worker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TheNeural Backend API",
    description="Backend service for ML project management with GCP integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Define allowed origins for CORS
origins = [
    "https://playground.theneural.in",   # Vercel Frontend
    "http://localhost:8601",     # Scratch Editor
        # Production Frontend
    # Production Frontend
    "https://playgroundai-backend-uaaur7no2a-uc.a.run.app",  # Backend URL
    "http://localhost:3000",   # Next.js dev server
    "http://localhost:8601",   # Another frontend port if used
]

# Add additional origins from environment variable if specified
if settings.cors_origin:
    # Handle multiple origins separated by commas
    additional_origins = [origin.strip() for origin in settings.cors_origin.split(',')]
    for origin in additional_origins:
        if origin and origin not in origins:
            origins.append(origin)

# Add CORS middleware - UPDATED CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # Allow listed origins
    allow_credentials=True,
    allow_methods=["*"],          # Allow all HTTP methods (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],          # Allow all headers
    expose_headers=["*"],         # Expose all headers
    max_age=86400,               # Cache preflight response for 24 hours
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # In production, restrict this
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# CORS debugging middleware
@app.middleware("http")
async def cors_debug_middleware(request: Request, call_next):
    """Debug middleware for CORS issues"""
    # Log CORS-related headers
    origin = request.headers.get("origin")
    if origin:
        logger.info(f"CORS request from origin: {origin}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request path: {request.url.path}")
        logger.info(f"Origin in allowed list: {origin in origins}")
    
    response = await call_next(request)
    
    # Log CORS response headers
    if origin:
        logger.info(f"CORS response headers: {dict(response.headers)}")
    
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "details": [str(exc)] if settings.node_env == "development" else []
        }
    )

# Include routers
app.include_router(health.router)
app.include_router(projects.router)
app.include_router(teachers.router)
app.include_router(students.router)
app.include_router(classrooms.router)
app.include_router(demo_projects.router)
app.include_router(guests_router)
app.include_router(scratch_services.router)

# Add explicit OPTIONS handler for CORS preflight
@app.options("/{full_path:path}")
async def options_handler(request: Request):
    """Handle OPTIONS requests for CORS preflight"""
    origin = request.headers.get("origin")
    logger.info(f"OPTIONS preflight request from origin: {origin}")
    logger.info(f"Allowed origins: {origins}")
    
    if origin in origins:
        logger.info(f"CORS preflight successful for origin: {origin}")
        return {
            "message": "CORS preflight successful",
            "allowed_origin": origin
        }
    else:
        logger.warning(f"CORS preflight failed for origin: {origin}")
        return {
            "message": "CORS preflight failed",
            "requested_origin": origin,
            "allowed_origins": origins
        }

def start_training_worker():
    """Start training worker in background thread"""
    try:
        logger.info("Starting training worker in background...")
        training_worker.start_worker()
    except Exception as e:
        logger.error(f"Failed to start training worker: {e}")

async def start_training_worker_async():
    """Start training worker in background thread (async)"""
    try:
        # Wait a bit for the server to be fully up
        await asyncio.sleep(2)
        logger.info("Starting training worker in background (async)...")
        await asyncio.get_running_loop().run_in_executor(None, start_training_worker)
        logger.info("Training worker started in background (async)")
    except Exception as e:
        logger.error(f"Failed to start training worker (async): {e}")

async def check_spacy_model_async():
    """Check if spaCy model is available (async)"""
    try:
        await asyncio.sleep(1)  # Small delay to not block startup
        import spacy
        nlp = spacy.load("en_core_web_sm")
        logger.info("✅ spaCy English model loaded successfully (async)")
    except ImportError:
        logger.info("📝 spaCy not installed yet - will install when needed (async)")
    except OSError:
        logger.info("📥 spaCy model not downloaded yet - will download when needed (async)")
    except Exception as e:
        logger.warning(f"⚠️ spaCy model check failed (async): {e}")
        logger.info("📝 Model will be downloaded when first training request is made (async)")

# Startup event - Keep it lightweight for Cloud Run health checks
@app.on_event("startup")
async def startup_event():
    logger.info("Starting TheNeural Backend API...")
    logger.info(f"Environment: {settings.node_env}")
    logger.info(f"GCP Project: {settings.google_cloud_project}")
    logger.info(f"CORS Origin: {settings.cors_origin}")
    
    try:
        # Start background tasks without blocking startup
        asyncio.create_task(check_spacy_model_async())
        asyncio.create_task(start_training_worker_async())
        
        logger.info("✅ TheNeural Backend API startup complete - background tasks starting...")
    except Exception as e:
        logger.error(f"⚠️ Some background tasks failed to start: {e}")
        logger.info("📝 Application will continue without background tasks")
        # Don't fail startup - allow the app to run without background services

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down TheNeural Backend API...")

if __name__ == "__main__":
    import uvicorn
    # Use PORT environment variable for Cloud Run compatibility, default to 8080
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.node_env == "development"
    )