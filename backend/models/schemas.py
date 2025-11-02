"""Pydantic models for request/response validation."""
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


class AudioAnalysisRequest(BaseModel):
    """Request model for audio analysis."""
    sample_rate: int = Field(..., description="Audio sample rate in Hz")
    uid: str = Field(..., description="User ID")
    analyze_emotion: bool = Field(True, description="Whether to analyze emotions")
    save_to_gcs: bool = Field(True, description="Whether to save to GCS")
    send_notification: Optional[bool] = Field(None, description="Override notification setting")
    emotion_filters: Optional[str] = Field(None, description="JSON emotion filters")


class TextAnalysisRequest(BaseModel):
    """Request model for text emotion analysis."""
    text: str = Field(..., max_length=10000, description="Text to analyze")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional metadata")


class EmotionConfigRequest(BaseModel):
    """Request model for updating emotion configuration."""
    notification_enabled: bool = Field(..., description="Enable/disable notifications")
    emotion_thresholds: Dict[str, float] = Field(..., description="Emotion thresholds")


class EmotionPrediction(BaseModel):
    """Emotion prediction data."""
    name: str
    score: float


class AudioAnalysisResponse(BaseModel):
    """Response model for audio analysis."""
    message: str
    filename: str
    uid: str
    sample_rate: int
    data_size_bytes: int
    timestamp: str
    local_file_path: str
    gcs_path: Optional[str] = None
    hume_analysis: Optional[Dict[str, Any]] = None


class AnalyticsStats(BaseModel):
    """Analytics statistics model."""
    total_requests: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0
    last_request_time: Optional[str] = None
    last_uid: Optional[str] = None
    recent_emotions: List[str] = Field(default_factory=list)
    emotion_counts: Dict[str, int] = Field(default_factory=dict)
    rizz_score: float = 75.0
    recent_notifications: List[Dict[str, Any]] = Field(default_factory=list)


class NotificationData(BaseModel):
    """Notification data model."""
    timestamp: str
    uid: str
    message: str


class StatusResponse(BaseModel):
    """Server status response."""
    status: str
    service: str
    configuration: Dict[str, bool]
    stats: AnalyticsStats
