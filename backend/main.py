"""
Emotion AI Platform

A comprehensive emotion analysis platform with:
- Audio Edge API: Original /audio endpoint for Omi devices with notifications
- Audio Analytics API: Stream endpoint for emotion analytics without notifications
- Dashboard API: Configuration and management
- Web Dashboard: Interactive UI for analytics and insights
"""
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.api import audio_edge, audio_analytics, dashboard, timeseries
from backend.utils.background_tasks import emotion_memory_background_task, cleanup_old_audio_files
from backend.core.config import Config

# Create FastAPI app
app = FastAPI(
    title="Emotion AI Platform",
    description="Emotion analysis platform with Hume AI integration",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(audio_edge.router)
app.include_router(audio_analytics.router)
app.include_router(dashboard.router)
app.include_router(timeseries.router)


@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on server startup."""
    print("🚀 Emotion AI Platform Starting...")
    print(f"   - Hume AI: {'✓ Configured' if Config.is_hume_configured() else '✗ Not configured'}")
    print(f"   - GCS: {'✓ Configured' if Config.is_gcs_configured() else '✗ Not configured'}")
    print(f"   - Omi: {'✓ Configured' if Config.is_omi_configured() else '✗ Not configured'}")

    # Start background tasks
    print("🚀 Starting emotion memory background task (runs every 1 hour)...")
    asyncio.create_task(emotion_memory_background_task())

    print("🗑️  Starting audio file cleanup task (runs every 1 minute)...")
    asyncio.create_task(cleanup_old_audio_files())

    print("✓ Emotion AI Platform Ready!")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - redirect to dashboard."""
    return RedirectResponse(url="/api/docs")


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "emotion-ai-platform",
        "version": "2.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    print(f"Starting server on {Config.HOST}:{Config.PORT}")
    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT
    )
