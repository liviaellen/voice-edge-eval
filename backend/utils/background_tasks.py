"""Background tasks for periodic maintenance and operations."""
import asyncio
from backend.core.config import Config
from backend.core.storage import StorageManager
from backend.services.analytics import analytics_service
from backend.services.notification import NotificationService


async def emotion_memory_background_task():
    """
    Background task that saves emotion summaries every hour.

    This task automatically creates memories in Omi with emotion statistics
    for the last active user.
    """
    notification_service = NotificationService()

    while True:
        try:
            # Wait 1 hour (3600 seconds)
            await asyncio.sleep(Config.EMOTION_MEMORY_INTERVAL_SECONDS)

            print("⏰ Running hourly emotion memory save...")

            # Use last active user
            target_uid = analytics_service.stats.last_uid

            if not target_uid:
                print("⚠️ No user ID available for emotion memory")
                continue

            # Generate emotion summary
            summary = analytics_service.generate_emotion_summary()

            if not summary["success"]:
                print(f"⚠️ Cannot create memory: {summary.get('error')}")
                continue

            # Create memory in Omi
            result = await notification_service.create_memory(
                uid=target_uid,
                text=summary["summary"],
                emotions=summary["emotions"]
            )

            if result.get("success"):
                print("✓ Hourly emotion memory saved successfully")
            else:
                print(f"⚠️ Hourly emotion memory save failed: {result.get('error')}")

        except Exception as e:
            print(f"Error in emotion memory background task: {e}")
            import traceback
            traceback.print_exc()


async def cleanup_old_audio_files():
    """
    Background task that deletes audio files older than configured age.

    Runs every minute to prevent disk space bloat.
    """
    storage = StorageManager()

    while True:
        try:
            # Run cleanup every 1 minute
            await asyncio.sleep(Config.CLEANUP_INTERVAL_SECONDS)

            deleted_count = storage.cleanup_old_files(Config.AUDIO_CLEANUP_AGE_SECONDS)

            if deleted_count > 0:
                print(f"🗑️  Cleaned up {deleted_count} old audio files")

        except Exception as e:
            print(f"Error in audio cleanup background task: {e}")
            import traceback
            traceback.print_exc()
