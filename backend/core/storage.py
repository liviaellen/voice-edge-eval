"""Storage management for audio files (local and cloud)."""
import os
import base64
import json
from pathlib import Path
from typing import Optional
from google.cloud import storage
from google.oauth2 import service_account

from backend.core.config import Config


class StorageManager:
    """Manages local and cloud storage for audio files."""

    def __init__(self):
        self.audio_dir = Path(Config.AUDIO_DIR)
        self.audio_dir.mkdir(exist_ok=True)
        self._gcs_client = None

    def save_audio_locally(self, filename: str, audio_data: bytes) -> Path:
        """
        Save audio file to local storage.

        Args:
            filename: Name of the file
            audio_data: Binary audio data

        Returns:
            Path to the saved file
        """
        file_path = self.audio_dir / filename

        with open(file_path, 'wb') as f:
            f.write(audio_data)

        print(f"✓ Saved audio file locally: {file_path}")
        return file_path

    async def upload_to_gcs(
        self,
        file_path: str,
        bucket_name: str,
        destination_blob_name: str
    ) -> Optional[str]:
        """
        Upload a file to Google Cloud Storage.

        Args:
            file_path: Path to the local file
            bucket_name: GCS bucket name
            destination_blob_name: Name for the blob in GCS

        Returns:
            GCS path of the uploaded file, or None if upload fails
        """
        if not Config.is_gcs_configured():
            print("⚠️ GCS not configured, skipping upload")
            return None

        try:
            # Get credentials from environment variable
            credentials_json = Config.GOOGLE_APPLICATION_CREDENTIALS_JSON
            if not credentials_json:
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not set")

            # Decode base64 credentials
            try:
                credentials_dict = json.loads(base64.b64decode(credentials_json))
                credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            except Exception as e:
                raise ValueError(f"Failed to decode credentials: {e}")

            # Create GCS client
            if not self._gcs_client:
                self._gcs_client = storage.Client(
                    credentials=credentials,
                    project=credentials_dict.get('project_id')
                )

            bucket = self._gcs_client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)

            # Upload file
            blob.upload_from_filename(file_path, content_type='audio/wav')

            gcs_path = f"gs://{bucket_name}/{destination_blob_name}"
            print(f"✓ Uploaded to GCS: {gcs_path}")
            return gcs_path

        except Exception as e:
            print(f"❌ Failed to upload to GCS: {e}")
            import traceback
            traceback.print_exc()
            return None

    def cleanup_old_files(self, max_age_seconds: int = 300) -> int:
        """
        Delete audio files older than specified age.

        Args:
            max_age_seconds: Maximum file age in seconds (default: 5 minutes)

        Returns:
            Number of files deleted
        """
        import time

        if not self.audio_dir.exists():
            return 0

        current_time = time.time()
        deleted_count = 0

        # Check all wav files in audio_files directory
        for audio_file in self.audio_dir.glob("*.wav"):
            try:
                # Get file age in seconds
                file_age = current_time - audio_file.stat().st_mtime

                # Delete if older than max age
                if file_age > max_age_seconds:
                    audio_file.unlink()
                    deleted_count += 1
                    print(f"🗑️  Deleted old audio file: {audio_file.name} (age: {file_age/60:.1f} minutes)")

            except Exception as e:
                print(f"Warning: Could not delete audio file {audio_file}: {e}")

        if deleted_count > 0:
            print(f"✓ Cleanup complete: Deleted {deleted_count} audio file(s)")

        return deleted_count


def create_wav_header(sample_rate: int, data_size: int) -> bytes:
    """
    Create a WAV file header for the audio data.

    Args:
        sample_rate: Audio sample rate in Hz (typically 8000 or 16000)
        data_size: Size of the audio data in bytes

    Returns:
        44-byte WAV header
    """
    num_channels = 1  # Mono
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8

    # RIFF header
    header = bytearray()
    header.extend(b'RIFF')
    header.extend((36 + data_size).to_bytes(4, 'little'))
    header.extend(b'WAVE')

    # fmt subchunk
    header.extend(b'fmt ')
    header.extend((16).to_bytes(4, 'little'))  # Subchunk size
    header.extend((1).to_bytes(2, 'little'))   # Audio format (PCM)
    header.extend(num_channels.to_bytes(2, 'little'))
    header.extend(sample_rate.to_bytes(4, 'little'))
    header.extend(byte_rate.to_bytes(4, 'little'))
    header.extend(block_align.to_bytes(2, 'little'))
    header.extend(bits_per_sample.to_bytes(2, 'little'))

    # data subchunk
    header.extend(b'data')
    header.extend(data_size.to_bytes(4, 'little'))

    return bytes(header)
