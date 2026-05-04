# SuicaPenguinChecker

JRE MALLのSuicaペンギン くたっとぬいぐるみの在庫状況を毎日チェックし、LINEに通知するシステム。

## 対象URL

https://shopping.jreast.co.jp/products/detail/s031/s031-G101173

## 構成

```
EventBridge cron (毎日18時JST)
    ↓
Lambda (suica-checker-trigger)
    ↓
ECS Fargate タスク起動
    ↓
ECRイメージ実行 (main.py)
  - JRE MALLをスクレイピング
  - Parameter Store からLINEトークン取得
    ↓
LINE Messaging API で通知
```

## ファイル構成

| ファイル | 説明 |
|---|---|
| `main.py` | メイン処理。スクレイピング + LINE通知 |
| `lambda_function.py` | Lambdaハンドラ。ECS RunTaskを呼び出すだけ |
| `Dockerfile` | python:3.12-slim ベース |
| `requirements.txt` | requests, beautifulsoup4, lxml, boto3 |
| `check_stock.py` | 動作確認用スクリプト（開発時のみ使用） |
| `test_line.py` | LINE通知動作確認用スクリプト（開発時のみ使用） |

## 在庫判定ロジック

`btn-discontinued` クラスのボタンが存在すれば在庫なし、`add-cart` クラスのボタンが存在すれば在庫あり。
両方のボタンがDOMに存在するケースがあるため、`btn-discontinued` を優先チェックする。

## AWS構成

| リソース | 名前/値 |
|---|---|
| ECRリポジトリ | `suica-checker` |
| ECSクラスター | `suica-checker` |
| ECSタスク定義 | `suica-checker:1` |
| Lambdaファンクション | `suica-checker-trigger` |
| EventBridgeルール | `suica-checker-daily` / `cron(0 9 * * ? *)` (JST 18時) |
| CloudWatch Logsグループ | `/ecs/suica-checker` |
| IAM タスクロール | `suica-checker-task-role` |
| IAM Lambdaロール | `suica-checker-lambda-role` |
| リージョン | `ap-northeast-1` (東京) |

## Parameter Store

| パラメータ名 | タイプ | 内容 |
|---|---|---|
| `/suica-checker/line-channel-token` | SecureString | LINE Messaging API チャネルアクセストークン |
| `/suica-checker/line-user-id` | String | LINE通知送信先のユーザーID |

## ローカル開発

```bash
# venv セットアップ
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 動作確認
LINE_CHANNEL_TOKEN="..." LINE_USER_ID="..." .venv/bin/python main.py

# コンテナビルド・実行
docker build --platform linux/amd64 -t suica-checker .
docker run --rm -e LINE_CHANNEL_TOKEN="..." -e LINE_USER_ID="..." suica-checker
```

## ECRへのデプロイ

```bash
aws ecr get-login-password --region ap-northeast-1 | \
  docker login --username AWS --password-stdin 781706644892.dkr.ecr.ap-northeast-1.amazonaws.com

docker build --platform linux/amd64 -t suica-checker .
docker tag suica-checker:latest 781706644892.dkr.ecr.ap-northeast-1.amazonaws.com/suica-checker:latest
docker push 781706644892.dkr.ecr.ap-northeast-1.amazonaws.com/suica-checker:latest
```

## 設定変更

### 実行時刻を変更する

```bash
aws events put-rule \
  --name suica-checker-daily \
  --schedule-expression "cron(0 9 * * ? *)" \
  --region ap-northeast-1
```

`cron(0 9 * * ? *)` の `9` がUTC時刻。JST = UTC+9。
