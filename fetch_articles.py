#!/usr/bin/env python3
"""
fetch_articles.py - NYT, Bloomberg, The Economist から記事を取得

Usage:
    python fetch_articles.py
    python fetch_articles.py --output /path/to/output.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import feedparser
import requests

# 出力ファイルのデフォルトパス
DEFAULT_OUTPUT_PATH = "/tmp/today_articles.json"

# NYT Top Stories API のセクション
NYT_SECTIONS = ["technology", "business", "world"]

# Bloomberg RSS フィード
BLOOMBERG_FEEDS = [
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://feeds.bloomberg.com/technology/news.rss",
    "https://feeds.bloomberg.com/politics/news.rss",
]

# The Guardian RSS フィード（Economistの代替 - Cloudflare保護のため）
GUARDIAN_FEEDS = [
    "https://www.theguardian.com/world/rss",
    "https://www.theguardian.com/business/rss",
    "https://www.theguardian.com/technology/rss",
]


def fetch_nyt_articles(api_key: str) -> list[dict[str, Any]]:
    """NYT Top Stories API から記事を取得"""
    articles = []

    for section in NYT_SECTIONS:
        url = f"https://api.nytimes.com/svc/topstories/v2/{section}.json"
        params = {"api-key": api_key}

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            for item in data.get("results", []):
                articles.append({
                    "source": "NYT",
                    "section": section,
                    "title": item.get("title", ""),
                    "abstract": item.get("abstract", ""),
                    "url": item.get("url", ""),
                    "published_date": item.get("published_date", ""),
                })
        except requests.RequestException as e:
            print(f"[ERROR] NYT {section} の取得に失敗: {e}", file=sys.stderr)
        except json.JSONDecodeError as e:
            print(f"[ERROR] NYT {section} のJSONパースに失敗: {e}", file=sys.stderr)

    return articles


def fetch_bloomberg_articles() -> list[dict[str, Any]]:
    """Bloomberg RSS フィードから記事を取得"""
    articles = []

    for feed_url in BLOOMBERG_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            section = _extract_section_from_url(feed_url)

            for entry in feed.entries:
                published = entry.get("published", "")
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6]).isoformat()

                articles.append({
                    "source": "Bloomberg",
                    "section": section,
                    "title": entry.get("title", ""),
                    "abstract": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "published_date": published,
                })
        except Exception as e:
            print(f"[ERROR] Bloomberg {feed_url} の取得に失敗: {e}", file=sys.stderr)

    return articles


def fetch_guardian_articles() -> list[dict[str, Any]]:
    """The Guardian RSS フィードから記事を取得"""
    articles = []

    for feed_url in GUARDIAN_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            section = _extract_guardian_section(feed_url)

            for entry in feed.entries:
                published = entry.get("published", "")
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6]).isoformat()

                # HTMLタグを除去した概要を取得
                abstract = entry.get("summary", "")
                # 簡易的にHTMLタグを除去
                import re
                abstract = re.sub(r'<[^>]+>', '', abstract)
                abstract = abstract[:500] if len(abstract) > 500 else abstract

                articles.append({
                    "source": "Guardian",
                    "section": section,
                    "title": entry.get("title", ""),
                    "abstract": abstract,
                    "url": entry.get("link", ""),
                    "published_date": published,
                })
        except Exception as e:
            print(f"[ERROR] Guardian {feed_url} の取得に失敗: {e}", file=sys.stderr)

    return articles


def _extract_guardian_section(url: str) -> str:
    """URLからセクション名を抽出"""
    if "world" in url:
        return "world"
    elif "business" in url:
        return "business"
    elif "technology" in url:
        return "technology"
    return "general"


def _extract_section_from_url(url: str) -> str:
    """URLからセクション名を抽出"""
    if "markets" in url:
        return "markets"
    elif "technology" in url:
        return "technology"
    elif "politics" in url:
        return "politics"
    return "general"


def filter_recent_articles(
    articles: list[dict[str, Any]],
    hours: int = 48
) -> list[dict[str, Any]]:
    """直近N時間以内の記事のみをフィルタリング"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    filtered = []

    for article in articles:
        pub_date_str = article.get("published_date", "")
        if not pub_date_str:
            # 日付がない場合は含める
            filtered.append(article)
            continue

        try:
            # ISO形式をパース
            pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)

            if pub_date >= cutoff:
                filtered.append(article)
        except ValueError:
            # パースできない場合は含める
            filtered.append(article)

    return filtered


def deduplicate_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """URLベースで重複を除去"""
    seen_urls = set()
    unique = []

    for article in articles:
        url = article.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(article)

    return unique


def main():
    parser = argparse.ArgumentParser(description="記事を取得してJSONに出力")
    parser.add_argument(
        "--output", "-o",
        default=DEFAULT_OUTPUT_PATH,
        help=f"出力ファイルパス (デフォルト: {DEFAULT_OUTPUT_PATH})"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=48,
        help="取得する記事の時間範囲（時間単位、デフォルト: 48）"
    )
    args = parser.parse_args()

    # NYT API キーを環境変数から取得
    nyt_api_key = os.environ.get("NYT_API_KEY")
    if not nyt_api_key:
        print("[ERROR] NYT_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    print("記事を取得中...")

    # 各ソースから記事を取得
    all_articles = []

    print("  - NYT Top Stories を取得中...")
    nyt_articles = fetch_nyt_articles(nyt_api_key)
    print(f"    -> {len(nyt_articles)} 件取得")
    all_articles.extend(nyt_articles)

    print("  - Bloomberg を取得中...")
    bloomberg_articles = fetch_bloomberg_articles()
    print(f"    -> {len(bloomberg_articles)} 件取得")
    all_articles.extend(bloomberg_articles)

    print("  - The Guardian を取得中...")
    guardian_articles = fetch_guardian_articles()
    print(f"    -> {len(guardian_articles)} 件取得")
    all_articles.extend(guardian_articles)

    # フィルタリングと重複除去
    print(f"\n直近 {args.hours} 時間の記事をフィルタリング...")
    filtered = filter_recent_articles(all_articles, hours=args.hours)
    print(f"  -> {len(filtered)} 件")

    print("重複を除去...")
    unique = deduplicate_articles(filtered)
    print(f"  -> {len(unique)} 件")

    # JSON出力
    output_data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total_count": len(unique),
        "articles": unique,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n{args.output} に {len(unique)} 件の記事を出力しました")


if __name__ == "__main__":
    main()
