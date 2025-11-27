import requests
import os
from dotenv import load_dotenv

load_dotenv() # 讀取 .env 檔案

# ------------------------------------------------------------------
# 請在 .env 檔案中設定你的 Discord Webhook 網址
# DISCORD_WEBHOOK_URL="your_discord_webhook_url_here"
# ------------------------------------------------------------------
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

def send_discord_msg(message):
    if not WEBHOOK_URL:
        print("警告: DISCORD_WEBHOOK_URL 未在 .env 檔案中設定，已跳過訊息發送。")
        return
    
    data = {
        "content": message,
        "username": "樹莓派 Anki 助教"
    }
    try:
        requests.post(WEBHOOK_URL, json=data)
    except Exception as e:
        print(f"Discord 發送失敗: {e}")

