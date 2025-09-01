"""
Production-ready FastAPI application with document processing endpoint.
"""

import json
import time
import logging
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any, Optional, List

import uvicorn
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import processing functions
from src.doc_extractor import extract_json_from_doc
from src.llm_parsing import add_translations
from src.text_to_speech import process_complete_dataset
from src.supabase_client import list_files, initialize_database, get_supabase_manager
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


class DocumentProcessingResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any] = {}
    processing_time: float
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
    
    # Initialize Supabase database
    try:
        logger.info("Initializing Supabase database...")
        if initialize_database():
            logger.info("✅ Supabase database initialized successfully")
        else:
            logger.warning("⚠️ Supabase database initialization failed, but continuing startup")
    except Exception as e:
        logger.error(f"❌ Error during Supabase initialization: {str(e)}")
        logger.warning("Continuing startup despite Supabase initialization error")
    
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


@app.get("/files", tags=["Files"])
async def get_files():
    """
    List all files stored in Supabase.
    
    Returns:
        List of file records from Supabase database
    """
    try:
        logger.info("📁 Retrieving files from Supabase")
        files = list_files()
        logger.info(f"Successfully retrieved {len(files)} files")
        
        return {
            "status": "success",
            "count": len(files),
            "files": files,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error retrieving files: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving files: {str(e)}"
        )


# Document processing endpoint
@app.post(
    "/process-document",
    response_model=DocumentProcessingResponse,
    responses={
        200: {"model": DocumentProcessingResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def process_document(
    file: UploadFile = File(..., description="DOCX file to process"),
    save_intermediate: bool = Form(
        False, 
        description="Whether to save intermediate processing results to disk"
    ),
):
    """
    Process a document through the extraction, translation, and TTS pipeline.
    
    - **file**: DOCX file to process
    - **save_intermediate**: If True, saves intermediate processing results to disk
    """
    start_time = time.time()
    
    # Validate file type
    if not file.filename.lower().endswith(('.docx')):
        raise HTTPException(
            status_code=400,
            detail="Only .docx files are supported"
        )
    
    try:
        # Save uploaded file to a temporary location
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        temp_file = temp_dir / file.filename
        with open(temp_file, "wb") as buffer:
            buffer.write(await file.read())
        
        # 1. Extract content from DOCX
        logger.info("Extracting content from DOCX...")
        extracted_data = extract_json_from_doc(str(temp_file))
        
        # 2. Add translations
        logger.info("Adding translations...")
        translated_data = add_translations(extracted_data)
        
        # 3. Generate TTS
        logger.info("Generating TTS files...")
        final_data = process_complete_dataset(translated_data)
        
        # 4. Get file URLs for all audio files
        logger.info("Retrieving file URLs...")
        supabase_manager = get_supabase_manager()
        
        # Collect all file IDs from the final data
        file_ids = set()
        
        def collect_file_ids(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if key.endswith('_speech_file_id') and value:
                        file_ids.add(value)
                    elif isinstance(value, (dict, list)):
                        collect_file_ids(value)
            elif isinstance(data, list):
                for item in data:
                    collect_file_ids(item)
        
        collect_file_ids(final_data)
        
        # Get URLs for all file IDs
        file_urls = supabase_manager.get_file_urls(list(file_ids))
        
        # Add URLs to the final data
        def add_urls_to_data(data, urls):
            if isinstance(data, dict):
                result = {}
                for key, value in data.items():
                    if key.endswith('_speech_file_id') and value and value in urls:
                        # Add URL for the file ID
                        url_key = key.replace('_file_id', '_url')
                        result[url_key] = urls[value]
                        result[key] = value  # Keep the original ID
                    elif isinstance(value, (dict, list)):
                        result[key] = add_urls_to_data(value, urls)
                    else:
                        result[key] = value
                return result
            elif isinstance(data, list):
                return [add_urls_to_data(item, urls) for item in data]
            return data
        
        final_data_with_urls = add_urls_to_data(final_data, file_urls)
        
        # Save results if requested
        if save_intermediate:
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            with open(output_dir / "extracted.json", "w", encoding="utf-8") as f:
                json.dump(extracted_data, f, indent=2, ensure_ascii=False)
            
            with open(output_dir / "translated.json", "w", encoding="utf-8") as f:
                json.dump(translated_data, f, indent=2, ensure_ascii=False)
            
            with open(output_dir / "final_output.json", "w", encoding="utf-8") as f:
                json.dump(final_data_with_urls, f, indent=2, ensure_ascii=False)
        
        # Clean up temp file
        temp_file.unlink()
        
        processing_time = time.time() - start_time
        
        return {
            "status": "success",
            "message": "Document processed successfully",
            "data": final_data_with_urls,
            "processing_time": processing_time,
            "timestamp": time.time(),
        }
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )

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