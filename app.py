"""
Production-ready FastAPI application with hello world and health check endpoints.
"""

import logging
import sys
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from utils.logger import get_logger

logger = get_logger(__name__)


# Response models
class HelloWorldResponse(BaseModel):
    message: str
    timestamp: float
    status: str = "success"


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: float
    version: str
    uptime_seconds: float


class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: float


# Global variables for tracking app state
app_start_time = time.time()
APP_VERSION = "1.0.0"


# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting FastAPI application...")
    logger.info(f" Application version: {APP_VERSION}")
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    logger.info("✅ Application shutdown complete")


# Create FastAPI instance
app = FastAPI(
    title="Production FastAPI App",
    description="A production-ready FastAPI application with hello world and health check endpoints",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Security middleware - Add trusted hosts
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Configure this for production with actual domains
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production with actual origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Custom middleware for request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing."""
    start_time = time.time()
    
    # Log request
    logger.info(f"📥 {request.method} {request.url.path} - Client: {request.client.host}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"📤 {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"❌ {request.method} {request.url.path} - Error: {str(e)} - Time: {process_time:.3f}s")
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"💥 Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            message="An unexpected error occurred",
            timestamp=time.time()
        ).dict()
    )


# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.warning(f"⚠️ HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=f"HTTP {exc.status_code}",
            message=exc.detail,
            timestamp=time.time()
        ).dict()
    )


# Routes
@app.get("/", response_model=HelloWorldResponse, tags=["Main"])
async def hello_world():
    """
    Hello World endpoint that returns a greeting message.
    
    Returns:
        HelloWorldResponse: JSON response with hello world message
    """
    logger.info("👋 Hello World endpoint called")
    
    response = HelloWorldResponse(
        message="Hello, World! 🌍",
        timestamp=time.time()
    )
    
    # Also print to console as requested
    print("Hello, World! 🌍")
    
    return response


@app.get("/health", response_model=HealthCheckResponse, tags=["Monitoring"])
async def health_check():
    """
    Health check endpoint for monitoring application status.
    
    Returns:
        HealthCheckResponse: JSON response with application health status
    """
    logger.info("🏥 Health check endpoint called")
    
    uptime = time.time() - app_start_time
    
    response = HealthCheckResponse(
        status="healthy",
        timestamp=time.time(),
        version=APP_VERSION,
        uptime_seconds=round(uptime, 2)
    )
    
    return response


# Additional utility endpoints for production monitoring
@app.get("/health/ready", tags=["Monitoring"])
async def readiness_check():
    """
    Readiness probe for Kubernetes/container orchestration.
    """
    return {"status": "ready", "timestamp": time.time()}


@app.get("/health/live", tags=["Monitoring"])
async def liveness_check():
    """
    Liveness probe for Kubernetes/container orchestration.
    """
    return {"status": "alive", "timestamp": time.time()}


@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """
    Basic application metrics endpoint.
    """
    uptime = time.time() - app_start_time
    return {
        "uptime_seconds": round(uptime, 2),
        "version": APP_VERSION,
        "timestamp": time.time(),
        "status": "operational"
    }


# Main entry point
if __name__ == "__main__":
    # Production-ready uvicorn configuration
    uvicorn.run(
        "app:app",  # This should match your filename
        host="0.0.0.0",
        port=8000,
        reload=True,  # Set to False in production
        workers=2,  # Adjust based on your server capacity
        log_level="info",
        access_log=True,
        server_header=False,  # Security: hide server info
        date_header=False,    # Security: hide date header
    )