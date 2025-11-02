"""Audio Analytics API - Stream endpoint without Omi notifications."""
from datetime import datetime
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Request, Query, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
import io

from backend.core.config import Config
from backend.core.emotion_analyzer import EmotionAnalyzer
from backend.core.storage import StorageManager, create_wav_header
from backend.services.analytics import analytics_service

router = APIRouter(prefix="/audio-analytics", tags=["Audio Analytics (Stream)"])

# Initialize services
storage = StorageManager()


@router.post("/analyze")
async def analyze_audio(
    request: Request,
    sample_rate: int = Query(..., description="Audio sample rate in Hz"),
    user_id: str = Query(..., description="User or session ID"),
    save_to_gcs: bool = Query(False, description="Whether to save audio to Google Cloud Storage"),
    include_full_analysis: bool = Query(True, description="Include full emotion breakdown")
):
    """
    Audio Analytics endpoint - Emotion analysis without notifications.

    This endpoint is designed for stream analytics and insights:
    - Analyzes emotions with Hume AI
    - Returns comprehensive emotion data
    - Does NOT send notifications to users
    - Tracks analytics for dashboard visualization
    - Optional GCS archival for compliance/training

    Query Parameters:
        - sample_rate: Audio sample rate (e.g., 8000 or 16000)
        - user_id: User or session identifier for tracking
        - save_to_gcs: Whether to archive audio to GCS (default: False)
        - include_full_analysis: Return full emotion breakdown vs top 3 (default: True)

    Body:
        - Binary audio data (application/octet-stream)

    Response:
        Returns detailed emotion analysis optimized for analytics dashboards

    Examples:
        POST /audio-analytics/analyze?sample_rate=16000&user_id=session_abc123
    """
    try:
        # Update stats
        analytics_service.increment_request(user_id)

        # Read audio bytes from request body
        audio_data = await request.body()

        if not audio_data:
            raise HTTPException(status_code=400, detail="No audio data received")

        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{user_id}_{timestamp}.wav"

        # Create WAV header
        wav_header = create_wav_header(sample_rate, len(audio_data))

        # Combine header and audio data
        wav_data = wav_header + audio_data

        # Save to local storage
        local_file_path = storage.save_audio_locally(filename, wav_data)

        try:
            # Analyze with Hume AI
            if not Config.is_hume_configured():
                raise HTTPException(status_code=503, detail="Hume AI not configured")

            print(f"[Analytics] Analyzing audio for user {user_id}")
            analyzer = EmotionAnalyzer(Config.HUME_API_KEY)
            hume_results = await analyzer.analyze_audio(str(local_file_path))
            print(f"[Analytics] Analysis complete: {hume_results.get('total_predictions', 0)} predictions")

            # Update stats
            if hume_results.get('success'):
                # Extract top emotions from predictions
                if hume_results.get('predictions'):
                    for pred in hume_results['predictions']:
                        if pred.get('top_3_emotions'):
                            analytics_service.record_success(pred['top_3_emotions'])
                            break
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

            # Build analytics response
            response_data = {
                "status": "success",
                "analysis_id": filename.replace('.wav', ''),
                "user_id": user_id,
                "timestamp": timestamp,
                "audio_metadata": {
                    "sample_rate": sample_rate,
                    "data_size_bytes": len(audio_data),
                    "duration_seconds": hume_results.get('total_duration_seconds'),
                    "chunked": hume_results.get('chunked', False)
                },
                "emotion_analysis": {
                    "success": hume_results.get('success', False),
                    "total_predictions": hume_results.get('total_predictions', 0),
                },
                "analytics": {
                    "rizz_score": analytics_service.stats.rizz_score,
                    "rizz_status": analytics_service.get_rizz_status_text(),
                    "recent_emotions": analytics_service.stats.recent_emotions
                }
            }

            # Include predictions based on detail level
            if hume_results.get('success'):
                if include_full_analysis:
                    response_data["emotion_analysis"]["predictions"] = hume_results.get('predictions', [])
                else:
                    # Just top 3 emotions from first prediction
                    if hume_results.get('predictions'):
                        first_pred = hume_results['predictions'][0]
                        response_data["emotion_analysis"]["top_emotions"] = first_pred.get('top_3_emotions', [])

            # Add error info if analysis failed
            if not hume_results.get('success'):
                response_data["emotion_analysis"]["error"] = hume_results.get('error', 'Unknown error')

            # Add GCS path if available
            if gcs_path:
                response_data["storage"] = {
                    "gcs_path": gcs_path,
                    "local_path": str(local_file_path.absolute())
                }

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
        print(f"[Analytics] Error processing audio: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/analyze-text")
async def analyze_text(
    request: Request,
    user_id: Optional[str] = Query(None, description="User or session ID (optional)")
):
    """
    Text Analytics endpoint - Emotion analysis from text.

    Analyzes emotional content based on word choice, phrasing, and linguistic patterns.
    Does NOT send notifications - designed for stream analytics.

    Query Parameters:
        - user_id: User or session identifier (optional)

    Body (JSON):
        {
            "text": "Your text to analyze here",
            "metadata": {...}  // optional metadata
        }

    Response:
        Detailed emotion analysis optimized for analytics dashboards

    Example:
        POST /audio-analytics/analyze-text?user_id=session_abc123
        Body: {"text": "I am feeling really happy and excited today!"}
    """
    try:
        # Parse JSON body
        body = await request.json()
        text = body.get('text')
        metadata = body.get('metadata', {})

        if not text:
            raise HTTPException(status_code=400, detail="Missing 'text' field in request body")

        # Check text length (API limit is 10,000 characters)
        if len(text) > 10000:
            raise HTTPException(
                status_code=400,
                detail=f"Text too long ({len(text)} characters). Maximum is 10,000 characters."
            )

        print(f"[Analytics] Analyzing text for user: {user_id or 'anonymous'}")
        print(f"[Analytics] Text length: {len(text)} characters")

        # Analyze text with Hume AI
        if not Config.is_hume_configured():
            raise HTTPException(status_code=503, detail="Hume AI not configured")

        analyzer = EmotionAnalyzer(Config.HUME_API_KEY)
        hume_results = await analyzer.analyze_text(text)

        response_data = {
            "status": "success" if hume_results.get('success') else "error",
            "user_id": user_id,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "text_metadata": {
                "length": len(text),
                "preview": text[:100] + "..." if len(text) > 100 else text
            },
            "emotion_analysis": hume_results,
            "metadata": metadata
        }

        return JSONResponse(
            status_code=200,
            content=response_data
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Analytics] Error analyzing text: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/stats")
async def get_analytics_stats():
    """
    Get current analytics statistics.

    Returns comprehensive statistics for the dashboard including:
    - Total requests and success/failure rates
    - Recent emotion trends
    - Rizz score and status
    - Emotion distribution

    Example:
        GET /audio-analytics/stats
    """
    try:
        return JSONResponse(
            status_code=200,
            content={
                "status": "online",
                "service": "emotion-ai-b2b",
                "stats": analytics_service.get_stats()
            }
        )
    except Exception as e:
        print(f"[Analytics] Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stats/reset")
async def reset_analytics_stats():
    """
    Reset all analytics statistics.

    ⚠️ This action cannot be undone.

    Example:
        POST /audio-analytics/stats/reset
    """
    try:
        analytics_service.reset_stats()
        return JSONResponse(
            status_code=200,
            content={
                "message": "Statistics reset successfully",
                "stats": analytics_service.get_stats()
            }
        )
    except Exception as e:
        print(f"[Analytics] Error resetting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_audio_file(
    file: UploadFile = File(...),
    user_id: str = Query(..., description="User or session ID"),
    save_to_gcs: bool = Query(False, description="Whether to save to GCS")
):
    """
    Upload audio file for emotion analysis.

    This endpoint accepts audio file uploads (WAV, MP3, M4A, etc.)
    and returns comprehensive emotion analysis.

    Query Parameters:
        - user_id: User or session identifier
        - save_to_gcs: Whether to archive to GCS (default: False)

    Body:
        - file: Audio file (multipart/form-data)

    Example:
        curl -X POST "http://localhost:8080/audio-analytics/upload?user_id=user123" \
          -F "file=@audio.wav"
    """
    try:
        # Update stats
        analytics_service.increment_request(user_id)

        # Read uploaded file
        audio_data = await file.read()

        if not audio_data:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        original_filename = file.filename or "upload.wav"
        file_extension = original_filename.split('.')[-1] if '.' in original_filename else 'wav'
        filename = f"{user_id}_{timestamp}.{file_extension}"

        # Save to local storage
        local_file_path = storage.audio_dir / filename
        with open(local_file_path, 'wb') as f:
            f.write(audio_data)

        print(f"[Analytics] Processing uploaded file: {filename} ({len(audio_data)} bytes)")

        try:
            # Convert to WAV if needed (for analysis)
            wav_file_path = local_file_path
            if file_extension.lower() != 'wav':
                # For non-WAV files, we'll need to convert
                # For now, assume WAV or let Hume handle it
                print(f"[Analytics] File type: {file_extension}")

            # Analyze with Hume AI
            if not Config.is_hume_configured():
                raise HTTPException(status_code=503, detail="Hume AI not configured")

            analyzer = EmotionAnalyzer(Config.HUME_API_KEY)
            hume_results = await analyzer.analyze_audio(str(wav_file_path))
            print(f"[Analytics] Upload analysis complete: {hume_results.get('total_predictions', 0)} predictions")

            # Update stats
            if hume_results.get('success'):
                if hume_results.get('predictions'):
                    for pred in hume_results['predictions']:
                        if pred.get('top_3_emotions'):
                            analytics_service.record_success(pred['top_3_emotions'])
                            break
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

            # Build response
            response_data = {
                "status": "success",
                "analysis_id": filename.replace(f'.{file_extension}', ''),
                "user_id": user_id,
                "timestamp": timestamp,
                "file_info": {
                    "original_filename": original_filename,
                    "file_size_bytes": len(audio_data),
                    "file_type": file_extension
                },
                "emotion_analysis": {
                    "success": hume_results.get('success', False),
                    "total_predictions": hume_results.get('total_predictions', 0),
                    "predictions": hume_results.get('predictions', [])
                },
                "analytics": {
                    "rizz_score": analytics_service.stats.rizz_score,
                    "rizz_status": analytics_service.get_rizz_status_text(),
                    "recent_emotions": analytics_service.stats.recent_emotions
                }
            }

            if not hume_results.get('success'):
                response_data["emotion_analysis"]["error"] = hume_results.get('error', 'Unknown error')

            if gcs_path:
                response_data["storage"] = {
                    "gcs_path": gcs_path,
                    "local_path": str(local_file_path.absolute())
                }

            return JSONResponse(status_code=200, content=response_data)

        except Exception as e:
            if local_file_path.exists():
                local_file_path.unlink()
            raise

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Analytics] Error processing upload: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.websocket("/stream")
async def websocket_audio_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio streaming and analysis.

    Connect to this endpoint to stream audio data in real-time
    and receive live emotion analysis results.

    Example client (JavaScript):
        const ws = new WebSocket('ws://localhost:8080/audio-analytics/stream');

        ws.onopen = () => {
            // Send metadata first
            ws.send(JSON.stringify({
                type: 'metadata',
                user_id: 'user123',
                sample_rate: 16000
            }));
        };

        // Then send audio chunks
        ws.send(audioChunkBuffer);
    """
    await websocket.accept()
    user_id = None
    sample_rate = 16000
    audio_chunks = []

    try:
        print("[Analytics] WebSocket connection established")

        while True:
            try:
                # Receive data from client
                data = await websocket.receive()

                if 'text' in data:
                    # Handle metadata/control messages
                    message = data['text']
                    try:
                        import json
                        msg_data = json.loads(message)

                        if msg_data.get('type') == 'metadata':
                            user_id = msg_data.get('user_id', 'unknown')
                            sample_rate = msg_data.get('sample_rate', 16000)
                            print(f"[Analytics] Stream metadata: user_id={user_id}, sample_rate={sample_rate}")

                            await websocket.send_json({
                                "type": "metadata_ack",
                                "status": "ready",
                                "user_id": user_id
                            })

                        elif msg_data.get('type') == 'analyze':
                            # Client requests analysis of accumulated audio
                            if not audio_chunks:
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "No audio data to analyze"
                                })
                                continue

                            print(f"[Analytics] Analyzing {len(audio_chunks)} audio chunks")

                            # Combine audio chunks
                            combined_audio = b''.join(audio_chunks)

                            # Create WAV file
                            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
                            filename = f"{user_id}_{timestamp}.wav"

                            wav_header = create_wav_header(sample_rate, len(combined_audio))
                            wav_data = wav_header + combined_audio

                            local_file_path = storage.save_audio_locally(filename, wav_data)

                            # Analyze
                            if Config.is_hume_configured():
                                analyzer = EmotionAnalyzer(Config.HUME_API_KEY)
                                hume_results = await analyzer.analyze_audio(str(local_file_path))

                                # Update stats
                                if hume_results.get('success'):
                                    if hume_results.get('predictions'):
                                        for pred in hume_results['predictions']:
                                            if pred.get('top_3_emotions'):
                                                analytics_service.record_success(pred['top_3_emotions'])
                                                break

                                # Send results back
                                await websocket.send_json({
                                    "type": "analysis_result",
                                    "status": "success",
                                    "emotion_analysis": hume_results,
                                    "analytics": {
                                        "rizz_score": analytics_service.stats.rizz_score,
                                        "rizz_status": analytics_service.get_rizz_status_text()
                                    }
                                })
                            else:
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "Hume AI not configured"
                                })

                            # Clear chunks
                            audio_chunks = []

                    except json.JSONDecodeError:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Invalid JSON message"
                        })

                elif 'bytes' in data:
                    # Handle audio data
                    audio_data = data['bytes']
                    audio_chunks.append(audio_data)

                    # Send acknowledgment
                    await websocket.send_json({
                        "type": "chunk_received",
                        "chunks_count": len(audio_chunks),
                        "total_bytes": sum(len(c) for c in audio_chunks)
                    })

            except WebSocketDisconnect:
                print(f"[Analytics] WebSocket disconnected for user: {user_id}")
                break
            except Exception as e:
                print(f"[Analytics] WebSocket error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

    except Exception as e:
        print(f"[Analytics] WebSocket connection error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await websocket.close()
        except:
            pass
