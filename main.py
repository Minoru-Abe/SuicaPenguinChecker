"""
Suicaペンギン くたっとぬいぐるみ 在庫チェッカー
- JRE MALLの商品ページをスクレイピング
- 在庫状況をLINE Messaging APIで通知
- 環境変数 or AWS Parameter Store から設定を取得
"""

import os
import sys
import boto3
import requests
from bs4 import BeautifulSoup

TARGET_URL = "https://shopping.jreast.co.jp/products/detail/s031/s031-G101173"
LINE_API_URL = "https://api.line.me/v2/bot/message/push"

SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9",
}


def get_config() -> dict:
    """
    設定を取得する。
    環境変数が設定されていればそちらを優先、なければ AWS Parameter Store から取得。
    """
    token = os.environ.get("LINE_CHANNEL_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")

    if token and user_id:
        return {"line_channel_token": token, "line_user_id": user_id}

    # AWS Parameter Store から取得
    ssm = boto3.client("ssm")
    token = ssm.get_parameter(
        Name="/suica-checker/line-channel-token", WithDecryption=True
    )["Parameter"]["Value"]
    user_id = ssm.get_parameter(
        Name="/suica-checker/line-user-id", WithDecryption=False
    )["Parameter"]["Value"]

    return {"line_channel_token": token, "line_user_id": user_id}


def check_stock() -> dict:
    """商品ページをスクレイピングして在庫状況を返す"""
    resp = requests.get(TARGET_URL, headers=SCRAPE_HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    # btn-discontinued クラスを優先チェック（add-cart は在庫なし時もDOMに存在するため）
    out_of_stock_btn = soup.find("button", class_="btn-discontinued")
    in_stock_btn = soup.find("button", class_="add-cart")

    if out_of_stock_btn:
        return {"in_stock": False, "message": "在庫なし"}
    elif in_stock_btn:
        return {"in_stock": True, "message": "在庫あり"}
    else:
        # 想定外のボタン状態（ページ構造変更などの可能性）
        return {"in_stock": None, "message": "状態不明（ページ構造を確認してください）"}


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
    resp.raise_for_status()


def build_message(stock: dict) -> str:
    if stock["in_stock"] is True:
        return (
            "🐧【在庫あり】Suicaのペンギン くたっとぬいぐるみ\n"
            "在庫がありました！！\n"
            f"{TARGET_URL}"
        )
    elif stock["in_stock"] is False:
        return (
            "【在庫なし】Suicaのペンギン くたっとぬいぐるみ\n"
            "本日も在庫なしでした。\n"
            f"{TARGET_URL}"
        )
    else:
        return f"【確認失敗】{stock['message']}\n{TARGET_URL}"


def main() -> None:
    config = get_config()
    stock = check_stock()

    print(f"[stock] {stock}")

    message = build_message(stock)
    send_line_message(config["line_channel_token"], config["line_user_id"], message)
    print("[done] LINE通知送信完了")


if __name__ == "__main__":
    main()
