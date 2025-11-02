"""Dashboard API - Configuration and management endpoints."""
import json
from typing import Optional
from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import JSONResponse

from backend.core.config import Config, emotion_config
from backend.services.analytics import analytics_service
from backend.services.notification import NotificationService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

notification_service = NotificationService()


@router.get("/config")
async def get_configuration():
    """
    Get current system configuration.

    Returns:
        System configuration including API status and emotion settings
    """
    return JSONResponse({
        "configuration": {
            "hume_ai": Config.is_hume_configured(),
            "google_cloud_storage": Config.is_gcs_configured(),
            "omi_integration": Config.is_omi_configured()
        },
        "emotion_config": emotion_config.config,
        "description": "System configuration and emotion notification settings"
    })


@router.get("/emotion-config")
async def get_emotion_config():
    """Get current emotion notification configuration."""
    return JSONResponse({
        "current_config": emotion_config.config,
        "description": "Automatic notification settings for detected emotions"
    })


@router.post("/emotion-config")
async def update_emotion_config(request: Request):
    """
    Update emotion notification configuration.

    Body (JSON):
    {
        "notification_enabled": true,
        "emotion_thresholds": {
            "Anger": 0.7,
            "Sadness": 0.6
        }
    }

    Note: Empty emotion_thresholds {} means notify for ALL emotions
    """
    try:
        new_config = await request.json()

        # Validate config
        if "notification_enabled" in new_config:
            if not isinstance(new_config["notification_enabled"], bool):
                raise HTTPException(status_code=400, detail="notification_enabled must be boolean")

        if "emotion_thresholds" in new_config:
            if not isinstance(new_config["emotion_thresholds"], dict):
                raise HTTPException(status_code=400, detail="emotion_thresholds must be a dict")

            # Validate thresholds are numbers between 0 and 1
            for emotion, threshold in new_config["emotion_thresholds"].items():
                if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Threshold for {emotion} must be between 0 and 1"
                    )

        # Update configuration
        emotion_config.update(new_config)

        print(f"✓ Updated emotion config: {emotion_config.config}")

        return JSONResponse({
            "message": "Configuration updated successfully",
            "new_config": emotion_config.config
        })

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except Exception as e:
        print(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/stats")
async def get_dashboard_stats():
    """
    Get comprehensive dashboard statistics.

    Returns analytics, emotion trends, and system health.
    """
    return JSONResponse({
        "status": "online",
        "service": "emotion-ai-platform",
        "configuration": {
            "hume_ai": Config.is_hume_configured(),
            "google_cloud_storage": Config.is_gcs_configured(),
            "omi_integration": Config.is_omi_configured()
        },
        "stats": analytics_service.get_stats(),
        "emotion_summary": analytics_service.generate_emotion_summary()
    })


@router.post("/stats/reset")
async def reset_dashboard_stats():
    """Reset all dashboard statistics."""
    analytics_service.reset_stats()
    return JSONResponse({
        "message": "Statistics reset successfully",
        "stats": analytics_service.get_stats()
    })


@router.post("/save-emotion-memory")
async def save_emotion_memory(
    uid: Optional[str] = Query(None, description="User ID (optional, uses last active if not provided)")
):
    """
    Manually save current emotion statistics to Omi memories.

    This creates a memory in Omi with the top detected emotions summary.
    Only works if Omi integration is configured.

    Query Parameters:
        - uid: User ID (optional, uses last active user if not provided)
    """
    # Use last active user if no uid provided
    target_uid = uid or analytics_service.stats.last_uid

    if not target_uid:
        return JSONResponse(
            status_code=400,
            content={
                "message": "No user ID available",
                "error": "No user ID available for emotion memory"
            }
        )

    # Generate emotion summary
    summary = analytics_service.generate_emotion_summary()

    if not summary["success"]:
        return JSONResponse(
            status_code=400,
            content={
                "message": "Failed to generate emotion summary",
                "error": summary.get("error")
            }
        )

    # Create memory in Omi
    result = await notification_service.create_memory(
        uid=target_uid,
        text=summary["summary"],
        emotions=summary["emotions"]
    )

    if result.get("success"):
        return JSONResponse(
            status_code=200,
            content={
                "message": "Emotion memory saved successfully",
                "result": result
            }
        )
    else:
        return JSONResponse(
            status_code=400,
            content={
                "message": "Failed to save emotion memory",
                "error": result.get("error")
            }
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns basic health status for monitoring and load balancers.
    """
    return JSONResponse({
        "status": "healthy",
        "service": "emotion-ai-platform"
    })
