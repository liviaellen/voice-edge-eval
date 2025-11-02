"""Audio Edge API - Original /audio endpoint for Omi devices with notifications."""
import json
from datetime import datetime
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import JSONResponse

from backend.core.config import Config, emotion_config
from backend.core.emotion_analyzer import EmotionAnalyzer
from backend.core.storage import StorageManager, create_wav_header
from backend.services.notification import NotificationService
from backend.services.analytics import analytics_service

router = APIRouter(prefix="/audio-edge", tags=["Audio Edge (Omi)"])

# Initialize services
storage = StorageManager()
notification_service = NotificationService()


@router.post("")
async def handle_audio_edge(
    request: Request,
    sample_rate: int = Query(..., description="Audio sample rate in Hz"),
    uid: str = Query(..., description="User ID"),
    analyze_emotion: bool = Query(True, description="Whether to analyze emotions with Hume AI"),
    save_to_gcs: bool = Query(True, description="Whether to save audio to Google Cloud Storage"),
    send_notification: Optional[bool] = Query(None, description="Override notification setting (uses config default if not specified)"),
    emotion_filters: Optional[str] = Query(None, description="Override emotion filters (uses config default if not specified)")
):
    """
    Audio Edge endpoint - Original /audio functionality for Omi devices.

    This endpoint:
    - Receives audio from Omi devices
    - Analyzes emotions with Hume AI
    - Sends notifications to Omi users based on emotion triggers
    - Saves audio to local storage and optionally to GCS

    Query Parameters:
        - sample_rate: Audio sample rate (e.g., 8000 or 16000)
        - uid: User unique ID
        - analyze_emotion: Whether to analyze emotions with Hume AI (default: True)
        - save_to_gcs: Whether to save audio to GCS (default: True)
        - send_notification: Whether to send Omi notification (default: uses config)
        - emotion_filters: JSON string of emotion:threshold pairs

    Body:
        - Binary audio data (application/octet-stream)

    Examples:
        # Basic emotion analysis
        POST /audio-edge?sample_rate=16000&uid=user123

        # With notification for any emotion
        POST /audio-edge?sample_rate=16000&uid=user123&send_notification=true
    """
    try:
        # Update stats
        analytics_service.increment_request(uid)

        # Read audio bytes from request body
        audio_data = await request.body()

        if not audio_data:
            raise HTTPException(status_code=400, detail="No audio data received")

        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{uid}_{timestamp}.wav"

        # Create WAV header
        wav_header = create_wav_header(sample_rate, len(audio_data))

        # Combine header and audio data
        wav_data = wav_header + audio_data

        # Save to local storage
        local_file_path = storage.save_audio_locally(filename, wav_data)

        try:
            # Analyze with Hume AI if requested
            hume_results = None
            if analyze_emotion:
                if not Config.is_hume_configured():
                    raise HTTPException(status_code=503, detail="Hume AI not configured")

                print(f"Analyzing audio with Hume AI for user {uid}")
                analyzer = EmotionAnalyzer(Config.HUME_API_KEY)
                hume_results = await analyzer.analyze_audio(str(local_file_path))
                print(f"Hume analysis complete: {hume_results.get('total_predictions', 0)} predictions")

                # Update stats
                if hume_results.get('success'):
                    # Extract top emotions from prosody predictions
                    if hume_results.get('predictions'):
                        for pred in hume_results['predictions']:
                            if pred.get('top_3_emotions'):
                                analytics_service.record_success(pred['top_3_emotions'])
                                break

                    # Check emotion triggers and send notification
                    should_notify = send_notification if send_notification is not None else emotion_config.get('notification_enabled', False)
                    print(f"🔔 Notification check: should_notify={should_notify}, has_predictions={bool(hume_results.get('predictions'))}")

                    if should_notify and hume_results.get('predictions'):
                        # Use emotion filters from parameter, or fall back to config
                        filters_dict = None
                        if emotion_filters:
                            try:
                                filters_dict = json.loads(emotion_filters)
                                print(f"Using custom emotion filters: {filters_dict}")
                            except json.JSONDecodeError as e:
                                print(f"Warning: Invalid emotion_filters JSON: {e}")
                                filters_dict = emotion_config.get('emotion_thresholds')
                        else:
                            filters_dict = emotion_config.get('emotion_thresholds')
                            print(f"Using config emotion filters: {filters_dict}")

                        # Check triggers
                        trigger_result = analytics_service.check_emotion_triggers(
                            hume_results['predictions'],
                            filters_dict
                        )
                        print(f"📊 Trigger check result: triggered={trigger_result['triggered']}, count={trigger_result['total_triggers']}")

                        if trigger_result['triggered']:
                            print(f"🔔 Emotion trigger detected! {trigger_result['total_triggers']} emotions matched")

                            # Format notification message
                            emotion_names = [e['name'] for e in trigger_result['emotions'][:3]]
                            notification_msg = NotificationService.generate_rizz_notification_message(
                                analytics_service.stats.rizz_score,
                                emotion_names
                            )

                            # Send notification
                            notification_result = await notification_service.send_notification(uid, notification_msg)

                            # Track notification
                            if notification_result.get('success'):
                                analytics_service.add_notification(uid, notification_msg)
                                print(f"✓ Notification sent successfully")
                            else:
                                print(f"✗ Notification failed: {notification_result.get('error')}")

                            # Add to response
                            hume_results['notification_sent'] = notification_result.get('success', False)
                            hume_results['triggered_emotions'] = trigger_result['emotions']
                        else:
                            print(f"ℹ️  No emotion triggers matched (filters: {filters_dict})")
                            hume_results['notification_sent'] = False
                            hume_results['trigger_check'] = "No emotions matched threshold"
                else:
                    analytics_service.record_failure()

            # Upload to GCS if requested
            gcs_path = None
            if save_to_gcs:
                bucket_name = Config.GCS_BUCKET_NAME
                if bucket_name:
                    gcs_path = await storage.upload_to_gcs(
                        str(local_file_path),
                        bucket_name,
                        filename
                    )

            response_data = {
                "message": "Audio processed successfully",
                "filename": filename,
                "uid": uid,
                "sample_rate": sample_rate,
                "data_size_bytes": len(audio_data),
                "timestamp": timestamp,
                "local_file_path": str(local_file_path.absolute())
            }

            # Add GCS path if available
            if gcs_path:
                response_data["gcs_path"] = gcs_path

            # Add Hume results if available
            if hume_results:
                response_data["hume_analysis"] = hume_results

            return JSONResponse(
                status_code=200,
                content=response_data
            )

        except Exception as e:
            # If there's an error, clean up the file
            if local_file_path.exists():
                local_file_path.unlink()
            raise

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing audio: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
