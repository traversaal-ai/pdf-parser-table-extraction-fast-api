"""
Main entrypoint for the Document Table Extractor API (FastAPI).
Sets up the application, logging, routers, CORS, and error handling.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers.extract import router as extract_router
from app.routers.health import router as health_router
from app.core.logging_config import configure_logging
from app.core.exceptions import ServiceError
import logging

# Configure logging
configure_logging()
_log = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Document Table Extractor API",
    description="Extract tables from documents and export to CSV/HTML formats",
    version="1.0.0"
)

# Enable CORS for API usability (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(extract_router)
app.include_router(health_router)

# Error handler for custom service errors
@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    _log.error(f"ServiceError: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

# Startup event handler
@app.on_event("startup")
async def on_startup():
    _log.info("Document Table Extractor API is starting up.")

# Shutdown event handler
@app.on_event("shutdown")
async def on_shutdown():
    _log.info("Document Table Extractor API is shutting down.")

