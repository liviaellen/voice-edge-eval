"""Omi notification service."""
import random
from typing import Dict, Any, List
from datetime import datetime, timezone
import httpx
from urllib.parse import quote

from backend.core.config import Config


class NotificationService:
    """Handles sending notifications to Omi users."""

    def __init__(self):
        self.app_id = Config.OMI_APP_ID
        self.api_key = Config.OMI_API_KEY

    async def send_notification(self, uid: str, message: str) -> Dict[str, Any]:
        """
        Send a direct notification to Omi user.

        Args:
            uid: Omi user ID
            message: The notification message

        Returns:
            Dict with success status and response
        """
        if not Config.is_omi_configured():
            return {
                "success": False,
                "error": "OMI_APP_ID or OMI_API_KEY not configured"
            }

        try:
            # Make API request to Omi notification endpoint
            url = f"https://api.omi.me/v2/integrations/{self.app_id}/notification?uid={quote(uid)}&message={quote(message)}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Content-Length": "0"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, timeout=30.0)

            if response.status_code >= 200 and response.status_code < 300:
                print(f"✓ Sent Omi notification to user {uid}")
                return {
                    "success": True,
                    "message": "Notification sent to Omi"
                }
            else:
                error_msg = f"Omi API error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }

        except Exception as e:
            print(f"Error sending Omi notification: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    async def create_memory(
        self,
        uid: str,
        text: str,
        emotions: List[Dict[str, Any]],
        timestamp: str = None
    ) -> Dict[str, Any]:
        """
        Create a memory in Omi based on detected emotions.

        Args:
            uid: Omi user ID
            text: The emotion summary text to save
            emotions: List of detected emotions
            timestamp: Optional timestamp

        Returns:
            Dict with success status and response
        """
        if not Config.is_omi_configured():
            return {
                "success": False,
                "error": "OMI_APP_ID or OMI_API_KEY not configured"
            }

        try:
            # Format emotions into a readable string
            emotion_list = ", ".join([f"{e['name']} ({e['score']:.2f})" for e in emotions[:3]])

            # Create memory data
            memory_data = {
                "memories": [
                    {
                        "content": f"Emotion detected: {emotion_list}",
                        "tags": ["emotion", "audio_analysis", emotions[0]['name'].lower()]
                    }
                ],
                "text": text,
                "text_source": "other",
                "text_source_spec": "emotion_ai_analysis"
            }

            # Make API request to Omi
            url = f"https://api.omi.me/v2/integrations/{self.app_id}/user/memories?uid={uid}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=memory_data, headers=headers, timeout=30.0)

            if response.status_code == 200:
                print(f"✓ Created Omi memory for user {uid}")
                return {
                    "success": True,
                    "message": "Memory created in Omi"
                }
            else:
                error_msg = f"Omi API error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }

        except Exception as e:
            print(f"Error creating Omi memory: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def generate_rizz_notification_message(score: float, emotions: List[str]) -> str:
        """
        Generate a notification message with rizz status and emotions.

        Args:
            score: Rizz score from 0 to 100
            emotions: List of emotion names (top 3)

        Returns:
            Formatted notification message
        """
        emotion_str = ", ".join(emotions)
        score_text = f"{score:.0f}%"

        # Low rizz (< 40) - motivational messages
        if score < 40:
            messages = [
                "Level up bro! 💪",
                "Time to bounce back! 🚀",
                "Keep your head up! 💯",
                "You got this! 🔥",
                "Comeback mode! ⚡"
            ]
            inspirational = random.choice(messages)
            return f"⚡ Rizz: {score_text} | {inspirational} | {emotion_str}"

        # Medium rizz (40-80) - neutral messages
        elif score <= 80:
            messages = [
                "Stay balanced! 🎯",
                "Keep going! 💫",
                "Stay steady! 🌊",
                "Keep vibing! ✨",
                "Stay cool! 😌"
            ]
            inspirational = random.choice(messages)
            return f"⚡ Rizz: {score_text} | {inspirational} | {emotion_str}"

        # High rizz (> 80) - positive messages
        else:
            messages = [
                "Killing it! 🔥",
                "You're on fire! ⚡",
                "Peak vibes! 💯",
                "Keep it up! 🚀",
                "Boss mode! 😎"
            ]
            inspirational = random.choice(messages)
            return f"⚡ Rizz: {score_text} | {inspirational} | {emotion_str}"
