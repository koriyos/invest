"""
📰 글로벌 경제 모닝 브리핑 봇 (완전 무료 버전)
RSS 피드로 뉴스 수집 → Gemini AI 요약 → 텔레그램 발송
"""

import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# ── 환경변수 ──────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

# ── RSS 피드 목록 (완전 무료) ──────────────────────────────
RSS_FEEDS = [
    # 증시/경제 전반
    ("증시/경제",   "https://feeds.reuters.com/reuters/businessNews"),
    ("증시/경제",   "https://www.cnbc.com/id/10001147/device/rss/rss.html"),
    ("증시/경제",   "https://feeds.bloomberg.com/markets/news.rss"),
    # 암호화폐
    ("암호화폐",    "https://cointelegraph.com/rss"),
    ("암호화폐",    "https://coindesk.com/arc/outboundfeeds/rss/"),
    # 거시경제/금리
    ("거시경제",    "https://feeds.reuters.com/reuters/USDollarRSSFeed"),
    ("거시경제",    "https://www.ft.com/rss/home/us"),
    # 원자재
    ("원자재",      "https://feeds.reuters.com/reuters/companyNews"),
]

# ── RSS 수집 ───────────────────────────────────────────────
def fetch_rss(url, category, max_items=4):
    articles = []
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")[:max_items]
        for item in items:
            title = item.findtext("title", "").strip()
            desc  = item.findtext("description", "").strip()[:200]
            if title:
                articles.append({"category": category, "title": title, "desc": desc})
    except Exception as e:
        print(f"  RSS 오류 ({url[:40]}...): {e}")
    return articles

def fetch_all_news():
    all_articles = []
    for category, url in RSS_FEEDS:
        items = fetch_rss(url, category)
        all_articles.extend(items)
        print(f"  [{category}] {len(items)}개 수집")
    return all_articles

# ── Gemini AI 요약 ─────────────────────────────────────────
def summarize_with_gemini(articles):
    news_text = ""
    for a in articles:
        news_text += f"[{a['category']}] {a['title']}\n{a['desc']}\n\n"

    today = datetime.now().strftime("%Y년 %m월 %d일")

    prompt = f"""아래는 오늘({today}) 수집된 글로벌 경제 뉴스입니다.
투자자 관점에서 핵심만 뽑아 한국어로 브리핑해주세요.

형식:
📊 글로벌 증시/주가
- 핵심 내용 2~3줄

₿ 암호화폐
- 핵심 내용 2~3줄

🏦 거시경제/금리
- 핵심 내용 2~3줄

🛢 원자재/유가
- 핵심 내용 2~3줄

⚡️ 오늘의 투자 주목 포인트
- 네가 판단하기에 오늘 가장 중요한 내용 2~3줄

마지막에 한 줄 총평도 추가해줘. 너무 딱딱하지 않게.

---
{news_text}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    resp = requests.post(
        url,
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

# ── 텔레그램 발송 ──────────────────────────────────────────
def send_telegram(text):
    today = datetime.now().strftime("%m/%d")
    message = f"🌅 *모닝 경제 브리핑 {today}*\n\n{text}"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"},
        timeout=10,
    )
    resp.raise_for_status()
    print("✅ 텔레그램 전송 완료!")

# ── 메인 ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("📡 RSS 뉴스 수집 중...")
    articles = fetch_all_news()
    print(f"   총 {len(articles)}개 기사 수집됨")

    print("🤖 Gemini 요약 중...")
    summary = summarize_with_gemini(articles)

    print("📨 텔레그램 전송 중...")
    send_telegram(summary)
