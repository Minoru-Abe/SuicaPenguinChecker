"""
スイカのぬいぐるみ在庫チェッカー (動作確認用)
まず requests で試し、Queue-it に弾かれるか確認する
"""

import requests
from bs4 import BeautifulSoup

TARGET_URL = "https://shopping.jreast.co.jp/products/detail/s031/s031-G101173"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9",
}


def check_stock() -> dict:
    session = requests.Session()
    resp = session.get(TARGET_URL, headers=HEADERS, allow_redirects=True, timeout=15)

    print(f"[status]  HTTP {resp.status_code}")
    print(f"[url]     {resp.url}")
    print(f"[content] {len(resp.text)} chars")

    # Queue-it 待合室に飛ばされているか確認
    if "queue-it.net" in resp.url or "queueit" in resp.text.lower():
        print("[result] Queue-it 待合室にリダイレクトされました → Playwright が必要")
        return {"reachable": False, "reason": "queue-it"}

    soup = BeautifulSoup(resp.text, "lxml")

    # ---- 在庫ボタンを探す (実際のHTML確認後に調整予定) ----
    # 候補1: ボタンテキストで判断
    buttons = soup.find_all("button")
    for btn in buttons:
        text = btn.get_text(strip=True)
        print(f"[button] {text!r}  class={btn.get('class')}")

    # 候補2: input[type=submit] も確認
    submits = soup.find_all("input", {"type": "submit"})
    for s in submits:
        print(f"[submit] value={s.get('value')!r}  class={s.get('class')}")

    # ページタイトルだけでも確認
    title = soup.find("title")
    print(f"[title]  {title.get_text(strip=True) if title else 'N/A'}")

    return {"reachable": True, "html_snippet": resp.text[:500]}


if __name__ == "__main__":
    check_stock()
