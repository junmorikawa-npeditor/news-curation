# News Curation Bot

NYT、Bloomberg、The Economist の記事から、NewsPicksの翻訳候補となりそうな記事を毎朝自動選定し、Slackに投稿するボットです。

## 構成

```
news-curation/
├── fetch_articles.py    # 記事取得スクリプト
├── select_articles.py   # Claude API で記事選定
├── post_to_slack.py     # Slack 投稿
├── prompt.txt           # 選定プロンプト
├── requirements.txt     # Python 依存関係
└── .github/
    └── workflows/
        └── daily_news.yml  # GitHub Actions ワークフロー
```

## セットアップ

### 1. リポジトリを作成

```bash
# 新しいリポジトリを作成するか、このディレクトリを既存のリポジトリに追加
cd news-curation
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/news-curation.git
git push -u origin main
```

### 2. APIキーを取得

#### NYT API Key
1. https://developer.nytimes.com/ にアクセス
2. アカウントを作成してログイン
3. 「Apps」→「New App」で新しいアプリを作成
4. 「Top Stories API」を有効化
5. 発行されたAPI Keyをコピー

#### Anthropic API Key
1. https://console.anthropic.com/ にアクセス
2. アカウントを作成してログイン
3. 「API Keys」でキーを生成
4. キーをコピー（一度しか表示されないので注意）

#### Slack Incoming Webhook URL
1. https://api.slack.com/apps にアクセス
2. 「Create New App」→「From scratch」
3. アプリ名（例: News Curation Bot）とワークスペースを選択
4. 「Incoming Webhooks」を有効化
5. 「Add New Webhook to Workspace」をクリック
6. 投稿先チャンネルを選択
7. 生成された Webhook URL をコピー

### 3. GitHub Secrets を設定

1. GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」に移動
2. 「New repository secret」で以下を追加:

| Name | Value |
|------|-------|
| `NYT_API_KEY` | NYTのAPIキー |
| `ANTHROPIC_API_KEY` | AnthropicのAPIキー |
| `SLACK_WEBHOOK_URL` | SlackのWebhook URL |

### 4. 動作確認

1. GitHubリポジトリの「Actions」タブに移動
2. 「Daily News Curation」ワークフローを選択
3. 「Run workflow」→「Run workflow」で手動実行
4. Slackチャンネルに投稿されることを確認

## ローカルでのテスト

```bash
# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定
export NYT_API_KEY="your_nyt_api_key"
export ANTHROPIC_API_KEY="your_anthropic_api_key"
export SLACK_WEBHOOK_URL="your_slack_webhook_url"

# 1. 記事を取得
python fetch_articles.py

# 2. 記事を選定（Claude API を使用）
python select_articles.py

# 3. Slack に投稿
python post_to_slack.py
```

## カスタマイズ

### 選定基準を変更する

`prompt.txt` を編集して、選定の優先テーマや基準を調整できます。

### 実行時間を変更する

`.github/workflows/daily_news.yml` の `cron` を編集:

```yaml
schedule:
  # UTC時間で指定（JSTはUTC+9）
  - cron: '0 22 * * *'  # UTC 22:00 = JST 07:00
```

### 記事ソースを追加する

`fetch_articles.py` の `BLOOMBERG_FEEDS` などに RSS フィード URL を追加できます。

## トラブルシューティング

### 「NYT_API_KEY が設定されていません」エラー
- GitHub Secrets に `NYT_API_KEY` が正しく設定されているか確認
- ローカル実行時は環境変数が設定されているか確認

### 「Claude API エラー」
- `ANTHROPIC_API_KEY` が正しいか確認
- APIクレジットが残っているか確認

### Slackに投稿されない
- Webhook URL が正しいか確認
- Webhook URLが有効期限切れになっていないか確認
- 投稿先チャンネルがアーカイブされていないか確認

## コスト目安

- **NYT API**: 無料（1日500リクエストまで）
- **Anthropic API**: 約$0.01〜0.05/実行（入力トークン数による）
- **GitHub Actions**: 無料枠内（月2,000分まで）

## ライセンス

MIT

Last updated: 2026-02-11
