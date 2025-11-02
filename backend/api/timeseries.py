"""Time-series emotion analysis API."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Request, Query, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydub import AudioSegment

from backend.core.config import Config
from backend.core.emotion_analyzer import EmotionAnalyzer
from backend.core.storage import StorageManager, create_wav_header
from backend.services.analytics import analytics_service

router = APIRouter(prefix="/timeseries", tags=["Time-Series Analysis"])

# Initialize services
storage = StorageManager()


def classify_emotion_sentiment(emotion_name: str) -> int:
    """
    Classify emotion as positive (+1), neutral (0), or negative (-1).

    Args:
        emotion_name: Name of the emotion

    Returns:
        1 for positive, 0 for neutral, -1 for negative
    """
    if emotion_name in Config.POSITIVE_EMOTIONS:
        return 1
    elif emotion_name in Config.NEGATIVE_EMOTIONS:
        return -1
    else:
        return 0


@router.post("/analyze")
async def analyze_timeseries(
    file: UploadFile = File(...),
    user_id: str = Query(..., description="User or session ID"),
    chunk_duration: int = Query(5, description="Duration of each chunk in seconds (5 or 10)", ge=5, le=10)
):
    """
    Time-series emotion analysis with chunking.

    Analyzes audio file by splitting it into chunks and predicting emotions
    for each time segment. Returns a timeline of emotions with timestamps.

    Query Parameters:
        - user_id: User or session identifier
        - chunk_duration: Duration of each chunk in seconds (5 or 10, default: 5)

    Response:
        {
            "timeline": [
                {
                    "timestamp": 0,
                    "duration": 5,
                    "emotions": [
                        {"name": "Joy", "score": 0.85, "sentiment": 1},
                        {"name": "Excitement", "score": 0.72, "sentiment": 1},
                        {"name": "Interest", "score": 0.65, "sentiment": 0}
                    ],
                    "dominant_sentiment": 1
                },
                ...
            ],
            "aggregation": {
                "total_duration": 30.5,
                "total_chunks": 7,
                "overall_sentiment": {
                    "positive_percentage": 65.5,
                    "neutral_percentage": 20.0,
                    "negative_percentage": 14.5,
                    "dominant": "positive"
                },
                "emotion_summary": {...}
            }
        }

    Example:
        curl -X POST "http://localhost:8080/timeseries/analyze?user_id=user123&chunk_duration=5" \
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

        print(f"[TimeSeries] Processing: {filename} ({len(audio_data)} bytes), chunk_duration={chunk_duration}s")

        try:
            # Load audio to get duration
            audio = AudioSegment.from_file(str(local_file_path))
            total_duration_ms = len(audio)
            total_duration_seconds = total_duration_ms / 1000.0

            print(f"[TimeSeries] Total duration: {total_duration_seconds:.2f}s")

            # Check Hume AI configuration
            if not Config.is_hume_configured():
                raise HTTPException(status_code=503, detail="Hume AI not configured")

            analyzer = EmotionAnalyzer(Config.HUME_API_KEY)

            # Split audio into chunks
            chunk_duration_ms = chunk_duration * 1000
            timeline = []
            chunk_files = []

            num_chunks = (total_duration_ms + chunk_duration_ms - 1) // chunk_duration_ms

            print(f"[TimeSeries] Splitting into {num_chunks} chunks of {chunk_duration}s")

            for i in range(0, total_duration_ms, chunk_duration_ms):
                start_ms = i
                end_ms = min(i + chunk_duration_ms, total_duration_ms)
                chunk_index = i // chunk_duration_ms

                # Extract chunk
                chunk = audio[start_ms:end_ms]
                chunk_duration_actual = len(chunk) / 1000.0

                # Save chunk as WAV
                chunk_filename = f"{user_id}_{timestamp}_chunk{chunk_index}.wav"
                chunk_path = storage.audio_dir / chunk_filename
                chunk.export(str(chunk_path), format="wav")
                chunk_files.append(chunk_path)

                print(f"[TimeSeries] Analyzing chunk {chunk_index + 1}/{num_chunks}: {start_ms/1000:.1f}s - {end_ms/1000:.1f}s")

                # Analyze chunk
                hume_results = await analyzer.analyze_audio(str(chunk_path))

                if hume_results.get('success') and hume_results.get('predictions'):
                    # Get top 3 emotions from first prediction
                    prediction = hume_results['predictions'][0]
                    top_3 = prediction.get('top_3_emotions', [])

                    # Add sentiment classification
                    emotions_with_sentiment = []
                    sentiment_sum = 0

                    for emotion in top_3:
                        sentiment = classify_emotion_sentiment(emotion['name'])
                        emotions_with_sentiment.append({
                            "name": emotion['name'],
                            "score": emotion['score'],
                            "sentiment": sentiment
                        })
                        sentiment_sum += sentiment * emotion['score']

                    # Determine dominant sentiment for this chunk
                    if sentiment_sum > 0.1:
                        dominant_sentiment = 1  # Positive
                    elif sentiment_sum < -0.1:
                        dominant_sentiment = -1  # Negative
                    else:
                        dominant_sentiment = 0  # Neutral

                    timeline.append({
                        "timestamp": start_ms / 1000.0,
                        "end_timestamp": end_ms / 1000.0,
                        "duration": chunk_duration_actual,
                        "emotions": emotions_with_sentiment,
                        "dominant_sentiment": dominant_sentiment,
                        "sentiment_score": sentiment_sum
                    })
                else:
                    # No emotions detected or analysis failed
                    print(f"[TimeSeries] Chunk {chunk_index + 1} analysis failed or no emotions detected")
                    timeline.append({
                        "timestamp": start_ms / 1000.0,
                        "end_timestamp": end_ms / 1000.0,
                        "duration": chunk_duration_actual,
                        "emotions": [],
                        "dominant_sentiment": 0,
                        "sentiment_score": 0,
                        "error": hume_results.get('error', 'No emotions detected')
                    })

                # Clean up chunk file
                try:
                    chunk_path.unlink()
                except:
                    pass

            # Calculate aggregation
            aggregation = calculate_aggregation(timeline, total_duration_seconds)

            # Build response
            response_data = {
                "status": "success",
                "user_id": user_id,
                "timestamp": timestamp,
                "file_info": {
                    "original_filename": original_filename,
                    "total_duration": total_duration_seconds,
                    "chunk_duration": chunk_duration,
                    "total_chunks": len(timeline)
                },
                "timeline": timeline,
                "aggregation": aggregation
            }

            # Update analytics
            if timeline:
                # Use overall sentiment for analytics
                overall_emotions = aggregation.get('top_emotions', [])
                if overall_emotions:
                    analytics_service.record_success(overall_emotions[:3])

            return JSONResponse(status_code=200, content=response_data)

        except Exception as e:
            if local_file_path.exists():
                local_file_path.unlink()
            raise

    except HTTPException:
        raise
    except Exception as e:
        print(f"[TimeSeries] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def calculate_aggregation(timeline: List[Dict[str, Any]], total_duration: float) -> Dict[str, Any]:
    """
    Calculate aggregation statistics from timeline.

    Args:
        timeline: List of time-series data points
        total_duration: Total audio duration in seconds

    Returns:
        Aggregation statistics
    """
    if not timeline:
        return {
            "total_duration": total_duration,
            "total_chunks": 0,
            "overall_sentiment": {
                "positive_percentage": 0,
                "neutral_percentage": 0,
                "negative_percentage": 0,
                "dominant": "neutral"
            },
            "emotion_summary": {}
        }

    # Count sentiments
    positive_count = sum(1 for t in timeline if t.get('dominant_sentiment') == 1)
    neutral_count = sum(1 for t in timeline if t.get('dominant_sentiment') == 0)
    negative_count = sum(1 for t in timeline if t.get('dominant_sentiment') == -1)
    total_count = len(timeline)

    # Calculate percentages
    positive_pct = (positive_count / total_count * 100) if total_count > 0 else 0
    neutral_pct = (neutral_count / total_count * 100) if total_count > 0 else 0
    negative_pct = (negative_count / total_count * 100) if total_count > 0 else 0

    # Determine dominant sentiment
    if positive_pct > negative_pct and positive_pct > neutral_pct:
        dominant = "positive"
    elif negative_pct > positive_pct and negative_pct > neutral_pct:
        dominant = "negative"
    else:
        dominant = "neutral"

    # Count all emotions across timeline
    emotion_counts = {}
    emotion_scores = {}

    for chunk in timeline:
        for emotion in chunk.get('emotions', []):
            name = emotion['name']
            score = emotion['score']

            if name not in emotion_counts:
                emotion_counts[name] = 0
                emotion_scores[name] = 0

            emotion_counts[name] += 1
            emotion_scores[name] += score

    # Calculate average scores and sort
    emotion_summary = []
    for name, count in emotion_counts.items():
        avg_score = emotion_scores[name] / count
        sentiment = classify_emotion_sentiment(name)

        emotion_summary.append({
            "name": name,
            "count": count,
            "average_score": avg_score,
            "total_score": emotion_scores[name],
            "sentiment": sentiment
        })

    # Sort by average score
    emotion_summary.sort(key=lambda x: x['average_score'], reverse=True)

    # Calculate average sentiment score
    avg_sentiment_score = sum(t.get('sentiment_score', 0) for t in timeline) / total_count if total_count > 0 else 0

    return {
        "total_duration": total_duration,
        "total_chunks": total_count,
        "overall_sentiment": {
            "positive_percentage": round(positive_pct, 2),
            "neutral_percentage": round(neutral_pct, 2),
            "negative_percentage": round(negative_pct, 2),
            "dominant": dominant,
            "average_sentiment_score": round(avg_sentiment_score, 3),
            "positive_chunks": positive_count,
            "neutral_chunks": neutral_count,
            "negative_chunks": negative_count
        },
        "emotion_summary": {
            "top_emotions": emotion_summary[:10],
            "total_unique_emotions": len(emotion_summary)
        },
        "sentiment_timeline": [
            {
                "timestamp": t['timestamp'],
                "sentiment": t.get('dominant_sentiment', 0),
                "score": t.get('sentiment_score', 0)
            }
            for t in timeline
        ]
    }
