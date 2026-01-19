# ローカル開発環境設計書

## 概要
本ドキュメントは、Docker、docker-composeを用いたローカル開発環境の設計を定義します。
フロントエンドはホストマシンで直接実行し、バックエンド、CDK、および開発支援ツール（MailHog、MinIO）はDockerコンテナで管理します。

## 開発環境の目標

### 原則
- **責務の分離**: バックエンド実行とインフラ管理を分離
- **開発効率**: フロントエンドはホストで実行し高速なホットリロード
- **本番環境の模倣**: MailHog（SMTP）、MinIO（S3互換）で本番サービスを再現
- **高速ツール**: uv、Biomeによる高速なツールチェーン

## 技術スタック

### Python環境
- **uv**: 高速Pythonパッケージ・プロジェクトマネージャー
- **Ruff**: 高速リンター・フォーマッター

### JavaScript/TypeScript環境
- **Biome**: 高速リンター・フォーマッター
- **Node.js v20 LTS**: ホストマシンにインストール

### インフラ管理
- **AWS CDK**: TypeScriptでインフラをコード管理

### 開発支援ツール
- **MailHog**: メール送信テスト用SMTPサーバー
- **MinIO**: S3互換オブジェクトストレージ

## アーキテクチャ

### 構成
```
┌─────────────────────────────────────────────────┐
│ Host Machine                                    │
│  - Frontend (Next.js) - Port: 3000             │
│  - Node.js v20, npm                            │
└─────────────────────────────────────────────────┘
           ↓ http://localhost:8000

┌─────────────────────────────────────────────────┐
│ Docker Compose                                  │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │ Backend (FastAPI) - Port: 8000           │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │ PostgreSQL - Port: 5432                  │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │ MailHog (SMTP) - Port: 1025, 8025       │  │
│  │  - SMTP: 1025                            │  │
│  │  - Web UI: 8025                          │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │ MinIO (S3) - Port: 9000, 9001           │  │
│  │  - API: 9000                             │  │
│  │  - Console: 9001                         │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │ CDK (インフラ管理) - profile: cdk        │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## 前提条件（ホストマシン）

### 必須ソフトウェア
- **Docker Desktop**: 最新版
- **Node.js**: v20 LTS以上
- **npm**: v10以上

### 推奨ソフトウェア
- **VSCode**: エディタ
- **AWS CLI**: AWSリソース確認用

## コンテナ設計

### 1. バックエンドコンテナ（FastAPI）

#### backend/Dockerfile.dev

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# uvインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 依存関係インストール
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

#### backend/pyproject.toml

```toml
[project]
name = "backend"
version = "0.1.0"
description = "FastAPI backend application"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy>=2.0.25",
    "alembic>=1.13.1",
    "psycopg2-binary>=2.9.9",
    "pydantic>=2.5.3",
    "pydantic-settings>=2.1.0",
    "boto3>=1.34.0",  # MinIO（S3互換）用
    "aiosmtplib>=3.0.0",  # メール送信用
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.4",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.14",
    "mypy>=1.8.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
```

### 2. PostgreSQLコンテナ

```
イメージ: postgres:16-alpine
ポート: 5432
ボリューム: postgres_data
```

### 3. MailHogコンテナ（メールテスト）

```
イメージ: mailhog/mailhog
ポート:
  - 1025: SMTP（アプリから送信）
  - 8025: Web UI（受信メール確認）
```

**用途:**
- 開発中のメール送信テスト
- 実際のメールサーバーを使わずにメールの内容を確認
- Web UIで送信されたメールを表示

**アクセス:**
- Web UI: http://localhost:8025

### 4. MinIOコンテナ（S3互換ストレージ）

```
イメージ: minio/minio
ポート:
  - 9000: S3 API
  - 9001: Management Console
コマンド: server /data --console-address ":9001"
ボリューム: minio_data
```

**用途:**
- S3互換のオブジェクトストレージ
- ファイルアップロード・ダウンロードのテスト
- 本番のS3を使わずにローカルでストレージ機能を検証

**アクセス:**
- Console: http://localhost:9001
- デフォルト認証情報:
  - Username: minioadmin
  - Password: minioadmin

### 5. CDKコンテナ（インフラ管理）

#### cdk/Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /cdk

# AWS CDK CLIのグローバルインストール
RUN npm install -g aws-cdk

# 依存関係インストール
COPY package*.json ./
RUN npm install

CMD ["sh"]
```

## docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/app_db
      - ENV=development
      # メール設定（MailHog）
      - SMTP_HOST=mailhog
      - SMTP_PORT=1025
      # S3設定（MinIO）
      - S3_ENDPOINT=http://minio:9000
      - S3_ACCESS_KEY=minioadmin
      - S3_SECRET_KEY=minioadmin
      - S3_BUCKET=app-bucket
    depends_on:
      - postgres
      - mailhog
      - minio

  postgres:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=app_db

  mailhog:
    image: mailhog/mailhog:latest
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"  # S3 API
      - "9001:9001"  # Management Console
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin

  cdk:
    build:
      context: ./cdk
      dockerfile: Dockerfile
    volumes:
      - ./cdk:/cdk
      - ~/.aws:/root/.aws:ro
    environment:
      - AWS_REGION=ap-northeast-1
    profiles:
      - cdk

volumes:
  postgres_data:
  minio_data:
```

## フロントエンド設定（ホスト実行）

### frontend/biome.json

```json
{
  "$schema": "https://biomejs.dev/schemas/1.5.0/schema.json",
  "organizeImports": {
    "enabled": true
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true
    }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "semicolons": "asNeeded"
    }
  }
}
```

### frontend/.env.local

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 開発ワークフロー

### 初回セットアップ

#### 1. リポジトリクローン
```bash
git clone <repository-url>
cd project-template
```

#### 2. すべてのサービス起動
```bash
docker-compose up -d
```

起動されるサービス:
- バックエンド (FastAPI)
- PostgreSQL
- MailHog
- MinIO

#### 3. MinIO初期設定（バケット作成）

MinIO Consoleにアクセス: http://localhost:9001
- Username: minioadmin
- Password: minioadmin

バケット作成:
1. "Buckets" → "Create Bucket"
2. Bucket Name: `app-bucket`
3. Create

または、CLIで作成:
```bash
docker-compose exec minio sh

# mc（MinIO Client）設定
mc alias set local http://localhost:9000 minioadmin minioadmin

# バケット作成
mc mb local/app-bucket

# 確認
mc ls local
```

#### 4. データベースマイグレーション
```bash
docker-compose exec backend uv run alembic upgrade head
```

#### 5. フロントエンドセットアップ（ホスト）
```bash
cd frontend
npm install
```

#### 6. フロントエンド起動（ホスト）
```bash
npm run dev
```

**完了！**

アクセス可能なURL:
- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MailHog Web UI: http://localhost:8025
- MinIO Console: http://localhost:9001

### 日常の開発フロー

#### すべてのサービス起動
```bash
docker-compose up -d
```

#### フロントエンド起動（ホスト）
```bash
cd frontend
npm run dev
```

#### ログ確認
```bash
# すべてのサービス
docker-compose logs -f

# 特定のサービス
docker-compose logs -f backend
docker-compose logs -f postgres
```

#### 終了時
```bash
# フロントエンド: Ctrl + C

# Dockerサービス
docker-compose down
```

## 開発支援ツールの使用方法

### MailHog（メールテスト）

#### バックエンドからメール送信（例）

```python
import aiosmtplib
from email.message import EmailMessage

async def send_email(to: str, subject: str, body: str):
    message = EmailMessage()
    message["From"] = "noreply@example.com"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname="mailhog",  # docker-compose内のサービス名
        port=1025,
    )
```

#### 送信メールの確認
1. http://localhost:8025 にアクセス
2. 送信されたメールがWeb UIに表示される
3. メール内容、件名、送信先を確認

### MinIO（S3互換ストレージ）

#### バックエンドからS3操作（例）

```python
import boto3
from botocore.client import Config

s3_client = boto3.client(
    "s3",
    endpoint_url="http://minio:9000",  # docker-compose内のサービス名
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin",
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)

# ファイルアップロード
s3_client.upload_file("local_file.txt", "app-bucket", "remote_file.txt")

# ファイルダウンロード
s3_client.download_file("app-bucket", "remote_file.txt", "downloaded_file.txt")

# ファイル一覧
response = s3_client.list_objects_v2(Bucket="app-bucket")
for obj in response.get("Contents", []):
    print(obj["Key"])
```

#### MinIO Consoleでの操作
1. http://localhost:9001 にアクセス
2. ログイン（minioadmin / minioadmin）
3. "Buckets" → "app-bucket" でファイルを確認
4. Web UIからファイルのアップロード・ダウンロード・削除が可能

## CDK（インフラ管理）の使用

### CDKコンテナ起動
```bash
docker-compose --profile cdk run --rm cdk sh
```

### CDK操作（コンテナ内）
```bash
# スタック一覧
cdk list

# 差分確認
cdk diff

# デプロイ
cdk deploy

# スタック削除
cdk destroy
```

### 終了
```bash
exit
```

## 依存関係管理

### バックエンド（uv）

```bash
docker-compose exec backend sh

# 依存関係追加
uv add fastapi

# 開発依存関係追加
uv add --dev pytest

# 同期
uv sync

# 更新
uv lock --upgrade && uv sync
```

### フロントエンド（npm / ホスト）

```bash
cd frontend

# 依存関係追加
npm install <package-name>

# 更新
npm update
```

## データベース管理

### マイグレーション（Alembic）

```bash
# マイグレーションファイル生成
docker-compose exec backend uv run alembic revision --autogenerate -m "Add user table"

# マイグレーション適用
docker-compose exec backend uv run alembic upgrade head

# ロールバック
docker-compose exec backend uv run alembic downgrade -1

# 履歴確認
docker-compose exec backend uv run alembic history
```

### シードデータ
```bash
docker-compose exec backend uv run python scripts/seed_data.py
```

### データベースリセット
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec backend uv run alembic upgrade head
```

## テスト実行

### バックエンド
```bash
docker-compose exec backend uv run pytest

# カバレッジ付き
docker-compose exec backend uv run pytest --cov=app --cov-report=html
```

### フロントエンド（ホスト）
```bash
cd frontend
npm test
```

## コード品質管理

### バックエンド（Ruff）

```bash
docker-compose exec backend sh

# フォーマット
uv run ruff format .

# リント
uv run ruff check .

# リント（自動修正）
uv run ruff check --fix .
```

### フロントエンド（Biome / ホスト）

```bash
cd frontend

# リント
npm run lint

# リント（自動修正）
npm run lint:fix

# フォーマット
npm run format
```

## 環境変数管理

### .env.example

```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=app_db

# Backend
ENV=development
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/app_db
SECRET_KEY=dev-secret-key

# SMTP（MailHog）
SMTP_HOST=mailhog
SMTP_PORT=1025

# S3（MinIO）
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=app-bucket
```

### frontend/.env.local.example

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## ディレクトリ構造

```
project-template/
├── backend/
│   ├── Dockerfile.dev
│   ├── pyproject.toml
│   ├── uv.lock
│   └── app/
├── frontend/
│   ├── package.json
│   ├── biome.json
│   ├── .env.local
│   └── src/
├── cdk/
│   ├── Dockerfile
│   ├── package.json
│   ├── biome.json
│   └── lib/
├── docker-compose.yml
└── docs/
```

## トラブルシューティング

### ポート競合

```bash
# 使用中ポート確認
lsof -i :3000   # フロントエンド
lsof -i :8000   # バックエンド
lsof -i :5432   # PostgreSQL
lsof -i :8025   # MailHog Web UI
lsof -i :9000   # MinIO API
lsof -i :9001   # MinIO Console

# プロセス停止
kill -9 <PID>
```

### MinIOにアクセスできない

```bash
# MinIOコンテナ状態確認
docker-compose ps minio

# ログ確認
docker-compose logs minio

# MinIOコンテナ再起動
docker-compose restart minio
```

### MailHogにメールが届かない

```bash
# MailHogコンテナ状態確認
docker-compose ps mailhog

# ログ確認
docker-compose logs mailhog

# バックエンドの環境変数確認
docker-compose exec backend env | grep SMTP
```

### データベース接続エラー

```bash
# PostgreSQL状態確認
docker-compose ps postgres

# 接続テスト
psql postgresql://postgres:postgres@localhost:5432/app_db -c "SELECT 1;"

# ボリュームリセット
docker-compose down -v
docker-compose up -d
```

## 本番環境との差異

| 項目 | ローカル | 本番 (AWS) |
|------|---------|-----------|
| フロントエンド | ホスト（開発サーバー） | AWS Amplify |
| バックエンド | Docker (uvicorn --reload) | ECS Fargate (Gunicorn) |
| データベース | PostgreSQL (Docker) | Aurora PostgreSQL |
| メールサーバー | MailHog | Amazon SES |
| オブジェクトストレージ | MinIO | Amazon S3 |
| インフラ管理 | CDKコンテナ（手動） | GitHub Actions → CDK |

## セキュリティ

### .gitignore

```gitignore
# 環境変数
.env.local
frontend/.env.local
cdk/.env

# Python
.venv/
__pycache__/

# Node.js
node_modules/
.next/
cdk.out/

# AWS
.aws/
*.pem

# IDEs
.vscode/settings.json
```

## 更新履歴
- 2026-01-19: 初版作成
