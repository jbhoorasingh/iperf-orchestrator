from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import logging

from app.database import engine, Base
from app.middleware.version import version_middleware
from app.routers import auth, agents, exercises, tasks, agent
from app.background import start_background_tasks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting up...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Start background tasks
    background_task = asyncio.create_task(start_background_tasks())
    logger.info("Background tasks started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    background_task.cancel()
    try:
        await background_task
    except asyncio.CancelledError:
        pass
    logger.info("Background tasks stopped")


# Create FastAPI app
app = FastAPI(
    title="Iperf Orchestrator API",
    description="Distributed iperf3 orchestration platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add version middleware
app.middleware("http")(version_middleware)

# Include routers
app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(exercises.router)
app.include_router(tasks.router)
app.include_router(agent.router)


@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"ok": True}


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": "Resource not found",
            "details": {"path": str(request.url.path)}
        }
    )


@app.exception_handler(409)
async def conflict_handler(request: Request, exc):
    """Handle 409 errors"""
    return JSONResponse(
        status_code=409,
        content={
            "error": "conflict",
            "message": "Resource conflict",
            "details": {"path": str(request.url.path)}
        }
    )


@app.exception_handler(426)
async def upgrade_required_handler(request: Request, exc):
    """Handle 426 errors"""
    return JSONResponse(
        status_code=426,
        content={
            "error": "upgrade_required",
            "message": "API version upgrade required",
            "details": {"path": str(request.url.path)}
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
