"""Configuration management for the Emotion AI platform."""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # API Keys
    HUME_API_KEY: str = os.getenv('HUME_API_KEY', '')
    OMI_APP_ID: str = os.getenv('OMI_APP_ID', '')
    OMI_API_KEY: str = os.getenv('OMI_API_KEY', '')

    # GCS Configuration
    GCS_BUCKET_NAME: str = os.getenv('GCS_BUCKET_NAME', '')
    GOOGLE_APPLICATION_CREDENTIALS_JSON: str = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON', '')

    # Server Configuration
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', '8080'))
    NGROK_URL: str = os.getenv('NGROK_URL', '')

    # Audio Processing
    MAX_AUDIO_CHUNK_MS: int = 4500  # 4.5 seconds (safe margin for 5s limit)
    AUDIO_CLEANUP_AGE_SECONDS: int = 300  # 5 minutes
    AUDIO_DIR: str = "audio_files"

    # Background Tasks
    EMOTION_MEMORY_INTERVAL_SECONDS: int = 3600  # 1 hour
    CLEANUP_INTERVAL_SECONDS: int = 60  # 1 minute

    # Emotion Categories
    POSITIVE_EMOTIONS = {
        "Joy", "Amusement", "Satisfaction", "Excitement", "Pride", "Triumph",
        "Relief", "Romance", "Desire", "Admiration", "Adoration", "Love",
        "Interest", "Realization", "Surprise"
    }

    NEGATIVE_EMOTIONS = {
        "Anger", "Sadness", "Fear", "Disgust", "Anxiety", "Distress",
        "Shame", "Guilt", "Embarrassment", "Contempt", "Disappointment",
        "Pain", "Awkwardness", "Boredom", "Confusion", "Doubt", "Tiredness"
    }

    NEUTRAL_EMOTIONS = {
        "Calmness", "Concentration", "Contemplation", "Determination"
    }

    @classmethod
    def is_hume_configured(cls) -> bool:
        """Check if Hume AI is configured."""
        return bool(cls.HUME_API_KEY)

    @classmethod
    def is_gcs_configured(cls) -> bool:
        """Check if Google Cloud Storage is configured."""
        return bool(cls.GCS_BUCKET_NAME and cls.GOOGLE_APPLICATION_CREDENTIALS_JSON)

    @classmethod
    def is_omi_configured(cls) -> bool:
        """Check if Omi integration is configured."""
        return bool(cls.OMI_APP_ID and cls.OMI_API_KEY)


class EmotionConfig:
    """Emotion notification configuration."""

    def __init__(self):
        self.config_file = Path("emotion_config.json")
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load emotion notification configuration from file or environment."""
        # Default configuration - empty thresholds = notify for ALL emotions
        default_config = {
            "notification_enabled": True,
            "emotion_thresholds": {}
        }

        # Try to load from file
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    print(f"✓ Loaded emotion config: {config.get('emotion_thresholds')}")
                    return config
            except Exception as e:
                print(f"Warning: Could not load emotion_config.json: {e}")
                return default_config

        # Try to load from environment variable
        env_config = os.getenv('EMOTION_NOTIFICATION_CONFIG')
        if env_config:
            try:
                config = json.loads(env_config)
                print(f"✓ Loaded emotion config from env: {config.get('emotion_thresholds')}")
                return config
            except Exception as e:
                print(f"Warning: Could not parse EMOTION_NOTIFICATION_CONFIG: {e}")

        print(f"ℹ️  Using default emotion config: {default_config['emotion_thresholds']}")
        return default_config

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)

    def update(self, new_config: Dict[str, Any]) -> None:
        """Update the configuration."""
        self.config.update(new_config)
        self._save_config()

    def _save_config(self) -> None:
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"✓ Saved emotion config: {self.config}")


# Global instances
emotion_config = EmotionConfig()
