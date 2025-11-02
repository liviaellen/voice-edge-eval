"""Hume AI emotion analysis integration."""
from typing import Dict, Any, List
from pathlib import Path
from hume import AsyncHumeClient
from hume.expression_measurement.stream.stream.types import Config as HumeConfig, StreamLanguage
from pydub import AudioSegment

from backend.core.config import Config


class EmotionAnalyzer:
    """Hume AI emotion analysis service."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = AsyncHumeClient(api_key=api_key)

    async def analyze_audio(self, wav_file_path: str) -> Dict[str, Any]:
        """
        Analyze audio file with Hume AI Speech Prosody model.

        Automatically chunks audio >5 seconds into smaller segments.

        Args:
            wav_file_path: Path to the WAV audio file

        Returns:
            Dict containing emotion predictions from Hume AI
        """
        try:
            # Load audio to get actual duration
            audio = AudioSegment.from_wav(wav_file_path)
            duration_ms = len(audio)
            duration_seconds = duration_ms / 1000.0

            print(f"Audio duration: {duration_ms}ms ({duration_seconds:.2f} seconds)")

            # If audio is within limit, send as-is
            if duration_ms <= 5000:
                print(f"✓ Audio is within 5s limit, analyzing directly")
                return await self._analyze_single_audio(wav_file_path)

            # Audio is too long, need to chunk
            print(f"⚠️  Audio is {duration_seconds:.1f}s, chunking into 4.5s segments...")
            return await self._analyze_chunked_audio(wav_file_path, audio, duration_ms)

        except Exception as e:
            print(f"Error analyzing audio with Hume: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "predictions": []
            }

    async def _analyze_single_audio(self, wav_file_path: str) -> Dict[str, Any]:
        """
        Analyze a single audio file (must be ≤5 seconds).

        Args:
            wav_file_path: Path to the WAV audio file

        Returns:
            Dict containing emotion predictions
        """
        try:
            # Config with only prosody model
            model_config = HumeConfig(prosody={})

            async with self.client.expression_measurement.stream.connect() as socket:
                result = await socket.send_file(wav_file_path, config=model_config)

                # Check if result is an error
                if hasattr(result, 'error'):
                    return {
                        "success": False,
                        "error": f"Hume API error: {result.error}",
                        "predictions": []
                    }

                # Check for warnings (like "No speech detected")
                warning_msg = None
                if result and hasattr(result, 'prosody') and result.prosody:
                    if hasattr(result.prosody, 'warning') and result.prosody.warning:
                        warning_msg = result.prosody.warning
                        print(f"  ⚠️  Hume API warning: {warning_msg}")

                # Extract prosody (speech emotion) predictions
                if result and hasattr(result, 'prosody') and result.prosody:
                    prosody_preds = result.prosody.predictions

                    if not prosody_preds:
                        error_msg = "No speech detected in audio"
                        if warning_msg:
                            error_msg = f"{error_msg} (Hume: {warning_msg})"
                        return {
                            "success": False,
                            "error": error_msg,
                            "predictions": [],
                            "warning": warning_msg
                        }

                    predictions = []
                    for prediction in prosody_preds:
                        # Sort emotions by score (highest first)
                        sorted_emotions = sorted(
                            prediction.emotions,
                            key=lambda e: e.score,
                            reverse=True
                        )

                        pred_data = {
                            "time": {
                                "begin": prediction.time.begin if hasattr(prediction.time, 'begin') else None,
                                "end": prediction.time.end if hasattr(prediction.time, 'end') else None
                            },
                            "emotions": [
                                {"name": emotion.name, "score": emotion.score}
                                for emotion in sorted_emotions
                            ],
                            "top_3_emotions": [
                                {"name": emotion.name, "score": emotion.score}
                                for emotion in sorted_emotions[:3]
                            ]
                        }
                        predictions.append(pred_data)

                    return {
                        "success": True,
                        "predictions": predictions,
                        "total_predictions": len(predictions)
                    }
                else:
                    return {
                        "success": False,
                        "error": "No prosody predictions returned from Hume API",
                        "predictions": []
                    }

        except Exception as e:
            print(f"Error in _analyze_single_audio: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "predictions": []
            }

    async def _analyze_chunked_audio(
        self,
        wav_file_path: str,
        audio: AudioSegment,
        duration_ms: int
    ) -> Dict[str, Any]:
        """
        Analyze audio by chunking into smaller segments.

        Args:
            wav_file_path: Path to the original WAV file
            audio: Loaded AudioSegment
            duration_ms: Duration in milliseconds

        Returns:
            Dict containing combined emotion predictions
        """
        chunks_data = []
        chunk_files = []

        try:
            # Split audio into chunks
            num_chunks = (duration_ms + Config.MAX_AUDIO_CHUNK_MS - 1) // Config.MAX_AUDIO_CHUNK_MS
            print(f"   Splitting into {num_chunks} chunks")

            for i in range(0, duration_ms, Config.MAX_AUDIO_CHUNK_MS):
                start_ms = i
                end_ms = min(i + Config.MAX_AUDIO_CHUNK_MS, duration_ms)

                chunk = audio[start_ms:end_ms]
                chunk_duration = len(chunk)

                # Save chunk to temporary file
                chunk_path = f"{wav_file_path}.chunk{i // Config.MAX_AUDIO_CHUNK_MS}.wav"
                chunk.export(chunk_path, format="wav")
                chunk_files.append(chunk_path)

                print(f"   Chunk {i // Config.MAX_AUDIO_CHUNK_MS + 1}/{num_chunks}: {start_ms}ms-{end_ms}ms ({chunk_duration}ms)")

                # Analyze chunk
                chunk_result = await self._analyze_single_audio(chunk_path)

                if chunk_result.get('success'):
                    # Adjust time offsets for each prediction
                    for pred in chunk_result['predictions']:
                        pred['time']['begin'] = pred['time']['begin'] + (start_ms / 1000.0) if pred['time']['begin'] else None
                        pred['time']['end'] = pred['time']['end'] + (start_ms / 1000.0) if pred['time']['end'] else None
                        pred['chunk_index'] = i // Config.MAX_AUDIO_CHUNK_MS

                    chunks_data.extend(chunk_result['predictions'])
                else:
                    print(f"   ⚠️  Chunk {i // Config.MAX_AUDIO_CHUNK_MS + 1} analysis failed: {chunk_result.get('error')}")

            # Combine results from all chunks
            if chunks_data:
                return {
                    "success": True,
                    "predictions": chunks_data,
                    "total_predictions": len(chunks_data),
                    "total_duration_seconds": duration_ms / 1000.0,
                    "num_chunks": num_chunks,
                    "chunked": True
                }
            else:
                return {
                    "success": False,
                    "error": "All chunks failed to analyze",
                    "predictions": [],
                    "debug_info": {
                        "num_chunks": num_chunks,
                        "total_duration_seconds": duration_ms / 1000.0
                    }
                }

        finally:
            # Clean up chunk files
            for chunk_file in chunk_files:
                try:
                    if Path(chunk_file).exists():
                        Path(chunk_file).unlink()
                except Exception as e:
                    print(f"Warning: Could not delete chunk file {chunk_file}: {e}")

    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text with Hume AI Language model for emotional content.

        Args:
            text: The text to analyze (e.g., transcription from speech-to-text)

        Returns:
            Dict containing emotion predictions for the text
        """
        try:
            # Config with language model for text emotion
            model_config = HumeConfig(language=StreamLanguage())

            async with self.client.expression_measurement.stream.connect() as socket:
                result = await socket.send_text(text, config=model_config)

                # Check for errors
                if hasattr(result, 'error'):
                    return {
                        "success": False,
                        "error": f"Hume API error: {result.error}",
                        "predictions": []
                    }

                # Extract language predictions
                if result and hasattr(result, 'language') and result.language:
                    lang_preds = result.language.predictions
                    print(f"✓ Got {len(lang_preds)} text emotion predictions")

                    predictions = []
                    for prediction in lang_preds:
                        # Sort emotions by score (highest first)
                        sorted_emotions = sorted(
                            prediction.emotions,
                            key=lambda e: e.score,
                            reverse=True
                        )

                        pred_data = {
                            "text": prediction.text if hasattr(prediction, 'text') else None,
                            "position": {
                                "begin": prediction.position.begin if hasattr(prediction, 'position') else None,
                                "end": prediction.position.end if hasattr(prediction, 'position') else None
                            },
                            "emotions": [
                                {"name": emotion.name, "score": emotion.score}
                                for emotion in sorted_emotions
                            ],
                            "top_3_emotions": [
                                {"name": emotion.name, "score": emotion.score}
                                for emotion in sorted_emotions[:3]
                            ]
                        }
                        predictions.append(pred_data)

                    return {
                        "success": True,
                        "predictions": predictions,
                        "total_predictions": len(predictions),
                        "analyzed_text": text
                    }
                else:
                    error_msg = "No language predictions returned from Hume API"
                    print(f"❌ {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "predictions": []
                    }

        except Exception as e:
            print(f"Error analyzing text with Hume: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "predictions": []
            }
