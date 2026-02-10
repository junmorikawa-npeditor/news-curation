#!/usr/bin/env python3
"""
post_to_slack.py - 選定結果を Slack に投稿

Usage:
    python post_to_slack.py
    python post_to_slack.py --input /path/to/selected.md
    python post_to_slack.py --message "カスタムメッセージ"
"""

import argparse
import os
import sys

import requests

# デフォルトパス
DEFAULT_INPUT_PATH = "/tmp/selected.md"


def post_to_slack(webhook_url: str, message: str) -> bool:
    """Slack Incoming Webhook にメッセージを投稿"""
    payload = {"text": message}

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"[ERROR] Slack投稿に失敗: {e}", file=sys.stderr)
        return False


def post_error_to_slack(webhook_url: str, error_message: str) -> bool:
    """エラー通知を Slack に投稿"""
    message = f":rotating_light: *記事キュレーションでエラーが発生しました*\n\n```\n{error_message}\n```"
    return post_to_slack(webhook_url, message)


def main():
    parser = argparse.ArgumentParser(description="Slack に投稿")
    parser.add_argument(
        "--input", "-i",
        default=DEFAULT_INPUT_PATH,
        help=f"入力Markdownファイルパス (デフォルト: {DEFAULT_INPUT_PATH})"
    )
    parser.add_argument(
        "--message", "-m",
        help="直接投稿するメッセージ（指定時は --input を無視）"
    )
    parser.add_argument(
        "--error",
        help="エラーメッセージとして投稿"
    )
    args = parser.parse_args()

    # Webhook URLを環境変数から取得
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("[ERROR] SLACK_WEBHOOK_URL が設定されていません", file=sys.stderr)
        sys.exit(1)

    # エラー通知モード
    if args.error:
        print(f"エラー通知を Slack に投稿中...")
        success = post_error_to_slack(webhook_url, args.error)
        sys.exit(0 if success else 1)

    # メッセージを決定
    if args.message:
        message = args.message
    else:
        # ファイルから読み込み
        if not os.path.exists(args.input):
            print(f"[ERROR] 入力ファイルが見つかりません: {args.input}", file=sys.stderr)
            sys.exit(1)

        with open(args.input, "r", encoding="utf-8") as f:
            message = f.read()

    if not message.strip():
        print("[WARNING] メッセージが空です", file=sys.stderr)
        sys.exit(0)

    # Slack に投稿
    print("Slack に投稿中...")

    # Slackのメッセージ長制限（40000文字）を考慮
    MAX_LENGTH = 39000
    if len(message) > MAX_LENGTH:
        print(f"[WARNING] メッセージが長すぎるため切り詰めます ({len(message)} -> {MAX_LENGTH})")
        message = message[:MAX_LENGTH] + "\n\n_(メッセージが長すぎるため省略されました)_"

    success = post_to_slack(webhook_url, message)

    if success:
        print("投稿完了")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
