import os
import logging
import requests
from app.config import settings

logger = logging.getLogger("telegram_notifier")

class TelegramNotifier:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = settings.TELEGRAM_ENABLED and bool(self.bot_token) and bool(self.chat_id)

    def send_alert(self, message: str, image_path: str = None) -> bool:
        if not self.enabled:
            logger.info(f"[Telegram Mock] {message}")
            return False

        try:
            if image_path and os.path.exists(image_path):
                url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
                with open(image_path, "rb") as photo:
                    data = {"chat_id": self.chat_id, "caption": message, "parse_mode": "HTML"}
                    files = {"photo": photo}
                    response = requests.post(url, data=data, files=files, timeout=10)
            else:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                payload = {"chat_id": self.chat_id, "text": message, "parse_mode": "HTML"}
                response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info("Telegram notification sent successfully.")
                return True
            else:
                logger.error(f"Failed to send Telegram notification: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
            return False

telegram_notifier = TelegramNotifier()

