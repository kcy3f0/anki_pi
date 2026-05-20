import requests
from ..config import DISCORD_WEBHOOK_URL

class NotificationService:
    @staticmethod
    def send_discord_message(content):
        if not DISCORD_WEBHOOK_URL:
            print("Warning: DISCORD_WEBHOOK_URL not set. Skipping notification.")
            return False
            
        payload = {"content": content}
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending Discord message: {e}")
            return False

    def format_reminder_message(self, total_count, folder_data):
        message_lines = []
        message_lines.append(f"🔔 **該背單字囉！**")
        message_lines.append(f"今天有 **{total_count}** 張卡片需要複習。")
        message_lines.append("")

        for folder, decks in folder_data.items():
            message_lines.append(f"📁 **{folder}**:")
            for deck, count in decks.items():
                message_lines.append(f"  - {deck}: {count} 張")

        return "\n".join(message_lines)
