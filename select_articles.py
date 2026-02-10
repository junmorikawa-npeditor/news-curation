#!/usr/bin/env python3
"""
select_articles.py - Claude API を使って記事を選定

Usage:
    python select_articles.py
    python select_articles.py --input /path/to/articles.json --output /path/to/selected.md
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic

# デフォルトパス
DEFAULT_INPUT_PATH = "/tmp/today_articles.json"
DEFAULT_OUTPUT_PATH = "/tmp/selected.md"
DEFAULT_PROMPT_PATH = Path(__file__).parent / "prompt.txt"

# Claude モデル
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096


def load_articles(input_path: str) -> dict:
    """記事JSONを読み込む"""
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_prompt(prompt_path: str) -> str:
    """選定プロンプトを読み込む"""
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def format_articles_for_prompt(articles_data: dict) -> str:
    """記事データをプロンプト用にフォーマット"""
    articles = articles_data.get("articles", [])

    lines = [f"## 記事リスト（{len(articles)}件）\n"]

    for i, article in enumerate(articles, 1):
        lines.append(f"### {i}. {article.get('title', 'タイトルなし')}")
        lines.append(f"- **メディア**: {article.get('source', '不明')}")
        lines.append(f"- **セクション**: {article.get('section', '不明')}")
        lines.append(f"- **公開日時**: {article.get('published_date', '不明')}")
        lines.append(f"- **URL**: {article.get('url', '')}")
        lines.append(f"- **概要**: {article.get('abstract', '概要なし')}")
        lines.append("")

    return "\n".join(lines)


def select_articles_with_claude(
    articles_data: dict,
    prompt_template: str,
    api_key: str
) -> str:
    """Claude API を使って記事を選定"""
    client = anthropic.Anthropic(api_key=api_key)

    # 記事データをフォーマット
    articles_text = format_articles_for_prompt(articles_data)

    # 今日の日付
    today = datetime.now(timezone.utc).strftime("%Y年%m月%d日")

    # プロンプトを構築
    user_message = f"""以下の記事リストから、選定基準に基づいて記事を選んでください。
今日の日付は {today} です。

{articles_text}
"""

    print(f"Claude API ({MODEL}) に選定をリクエスト中...")

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=prompt_template,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    # レスポンスからテキストを抽出
    result = ""
    for block in response.content:
        if block.type == "text":
            result += block.text

    return result


def main():
    parser = argparse.ArgumentParser(description="Claude API で記事を選定")
    parser.add_argument(
        "--input", "-i",
        default=DEFAULT_INPUT_PATH,
        help=f"入力JSONファイルパス (デフォルト: {DEFAULT_INPUT_PATH})"
    )
    parser.add_argument(
        "--output", "-o",
        default=DEFAULT_OUTPUT_PATH,
        help=f"出力Markdownファイルパス (デフォルト: {DEFAULT_OUTPUT_PATH})"
    )
    parser.add_argument(
        "--prompt", "-p",
        default=str(DEFAULT_PROMPT_PATH),
        help=f"プロンプトファイルパス (デフォルト: {DEFAULT_PROMPT_PATH})"
    )
    args = parser.parse_args()

    # APIキーを環境変数から取得
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] ANTHROPIC_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    # 入力ファイルの確認
    if not os.path.exists(args.input):
        print(f"[ERROR] 入力ファイルが見つかりません: {args.input}", file=sys.stderr)
        sys.exit(1)

    # プロンプトファイルの確認
    if not os.path.exists(args.prompt):
        print(f"[ERROR] プロンプトファイルが見つかりません: {args.prompt}", file=sys.stderr)
        sys.exit(1)

    try:
        # 記事を読み込み
        print(f"記事を読み込み中: {args.input}")
        articles_data = load_articles(args.input)
        article_count = len(articles_data.get("articles", []))
        print(f"  -> {article_count} 件の記事を読み込みました")

        if article_count == 0:
            print("[WARNING] 記事が0件です。選定をスキップします。", file=sys.stderr)
            # 空の結果を出力
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(":warning: 本日は選定対象の記事がありませんでした。")
            sys.exit(0)

        # プロンプトを読み込み
        print(f"プロンプトを読み込み中: {args.prompt}")
        prompt_template = load_prompt(args.prompt)

        # Claude API で選定
        result = select_articles_with_claude(articles_data, prompt_template, api_key)

        # 結果を出力
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)

        print(f"\n選定結果を {args.output} に出力しました")

    except anthropic.APIError as e:
        print(f"[ERROR] Claude API エラー: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSONパースエラー: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 予期せぬエラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
