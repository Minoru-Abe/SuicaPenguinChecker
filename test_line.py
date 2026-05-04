"""
LINE Messaging API 動作確認スクリプト
"""

import os
import requests

LINE_API_URL = "https://api.line.me/v2/bot/message/push"


def send_line_message(token: str, to: str, text: str) -> None:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": to,
        "messages": [{"type": "text", "text": text}],
    }
    resp = requests.post(LINE_API_URL, headers=headers, json=payload, timeout=10)
    print(f"[status] {resp.status_code}")
    print(f"[body]   {resp.text}")


if __name__ == "__main__":
    token = os.environ.get("LINE_CHANNEL_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")

    if not token or not user_id:
        print("環境変数 LINE_CHANNEL_TOKEN と LINE_USER_ID を設定してください")
        raise SystemExit(1)

    send_line_message(token, user_id, "テスト送信: Suicaペンギンチェッカー動作確認")
