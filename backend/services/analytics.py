"""Analytics and statistics service."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.core.config import Config
from backend.models.schemas import AnalyticsStats, NotificationData


class AnalyticsService:
    """Manages analytics and statistics for emotion detection."""

    def __init__(self):
        self.stats = AnalyticsStats()

    def increment_request(self, uid: str) -> None:
        """Increment total request count and update last activity."""
        self.stats.total_requests += 1
        self.stats.last_request_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        self.stats.last_uid = uid

    def record_success(self, emotions: List[Dict[str, Any]]) -> None:
        """
        Record a successful emotion analysis.

        Args:
            emotions: List of top emotions detected
        """
        self.stats.successful_analyses += 1

        # Extract top emotions for display
        if emotions:
            self.stats.recent_emotions = [
                f"{e['name']} ({e['score']:.2f})"
                for e in emotions
            ]

            # Track emotion counts for statistics
            for emotion in emotions:
                emotion_name = emotion['name']
                if emotion_name not in self.stats.emotion_counts:
                    self.stats.emotion_counts[emotion_name] = 0
                self.stats.emotion_counts[emotion_name] += 1

            # Update rizz score based on detected emotions
            self.update_rizz_score(emotions)
            print(f"📊 Rizz Score updated: {self.stats.rizz_score:.1f}")

    def record_failure(self) -> None:
        """Record a failed emotion analysis."""
        self.stats.failed_analyses += 1

    def update_rizz_score(self, emotions: List[Dict[str, Any]]) -> None:
        """
        Update rizz score based on detected emotions.

        Positive emotions add points, negative emotions subtract.
        Score ranges from 0 to 100 (starts at 75).

        Args:
            emotions: List of emotion dicts with 'name' and 'score'
        """
        adjustment = 0

        for emotion in emotions:
            emotion_name = emotion['name']
            emotion_score = emotion['score']  # 0-1 scale

            if emotion_name in Config.POSITIVE_EMOTIONS:
                # Positive emotions add to rizz (scaled by emotion intensity)
                adjustment += emotion_score * 10  # Max +10 per emotion
            elif emotion_name in Config.NEGATIVE_EMOTIONS:
                # Negative emotions subtract from rizz
                adjustment -= emotion_score * 10  # Max -10 per emotion
            # Neutral emotions don't change the score

        # Update the score and clamp to 0 to 100 range
        self.stats.rizz_score = max(0, min(100, self.stats.rizz_score + adjustment))

    def get_rizz_status_text(self, score: Optional[float] = None) -> str:
        """
        Get the rizz status text based on score.

        Args:
            score: Rizz score from 0 to 100 (uses current if not provided)

        Returns:
            Status text with emoji
        """
        if score is None:
            score = self.stats.rizz_score

        if score > 80:
            return "😎 Positive Vibes!"
        elif score >= 40:
            return "😐 Neutral Energy"
        else:
            return "😔 Negative Energy"

    def add_notification(self, uid: str, message: str) -> None:
        """
        Track a sent notification.

        Args:
            uid: User ID
            message: Notification message
        """
        notification_data = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "uid": uid,
            "message": message
        }

        self.stats.recent_notifications.insert(0, notification_data)
        # Keep only last 10 notifications
        self.stats.recent_notifications = self.stats.recent_notifications[:10]

    def generate_emotion_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of top 5 emotions from statistics.

        Returns:
            Dict with summary text and top emotions
        """
        if not self.stats.emotion_counts:
            return {
                "success": False,
                "error": "No emotion data available"
            }

        # Get top 5 emotions
        sorted_emotions = sorted(
            self.stats.emotion_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        total_count = sum(self.stats.emotion_counts.values())

        # Build summary text
        emotion_list = []
        emotions_data = []

        for emotion, count in sorted_emotions:
            percentage = (count / total_count * 100)
            emotion_list.append(f"{emotion} ({percentage:.1f}%)")
            emotions_data.append({
                "name": emotion,
                "score": percentage / 100,  # Convert to 0-1 scale
                "count": count
            })

        summary_text = f"📊 Emotion Summary - Top 5 emotions detected: {', '.join(emotion_list)}"

        return {
            "success": True,
            "summary": summary_text,
            "emotions": emotions_data,
            "total_detections": total_count
        }

    def reset_stats(self) -> None:
        """Reset all statistics to default values."""
        self.stats = AnalyticsStats()

    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics as dict."""
        return self.stats.dict()

    def check_emotion_triggers(
        self,
        predictions: List[Dict[str, Any]],
        emotion_filters: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Check if any emotions meet the threshold criteria.

        Args:
            predictions: List of emotion predictions from Hume
            emotion_filters: Dict of {emotion_name: threshold} to filter by
                            If None, returns all emotions

        Returns:
            Dict with triggered emotions and details
        """
        triggered_emotions = []

        for prediction in predictions:
            emotions = prediction.get('emotions', [])

            for emotion in emotions:
                emotion_name = emotion['name']
                emotion_score = emotion['score']

                # If no filters, include all
                if not emotion_filters:
                    triggered_emotions.append({
                        "name": emotion_name,
                        "score": emotion_score,
                        "time": prediction.get('time')
                    })
                    continue

                # Check if this emotion is in our filter list
                if emotion_name in emotion_filters:
                    triggered_emotions.append({
                        "name": emotion_name,
                        "score": emotion_score,
                        "time": prediction.get('time')
                    })

        return {
            "triggered": len(triggered_emotions) > 0,
            "emotions": triggered_emotions,
            "total_triggers": len(triggered_emotions)
        }


# Global analytics instance
analytics_service = AnalyticsService()
