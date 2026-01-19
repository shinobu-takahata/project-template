# バックエンドローカル開発環境構築 - 要求仕様

## 概要
Docker、docker-composeを用いたバックエンド開発環境を構築します。
バックエンド（FastAPI）、PostgreSQL、開発支援ツール（MailHog、MinIO）をコンテナで管理し、効率的な開発環境を実現します。

## 目標
- バックエンド開発環境のDocker化
- 本番環境を模倣した開発支援サービスの導入
- 高速な依存関係管理（uv）の実装
- レイヤードアーキテクチャに基づくFastAPIサンプルコードの実装
- 開発者が`docker-compose up -d`で即座に開発開始できる状態の構築

## 実装対象

### 1. バックエンドコンテナ（FastAPI）
- **技術スタック**: Python 3.11、FastAPI、uvicorn
- **パッケージマネージャー**: uv
- **リンター/フォーマッター**: Ruff
- **ホットリロード**: 有効
- **ポート**: 8000

### 2. PostgreSQLコンテナ
- **イメージ**: postgres:16-alpine
- **ポート**: 5432
- **データ永続化**: Docker volume使用

### 3. MailHogコンテナ（メール送信テスト）
- **イメージ**: mailhog/mailhog
- **ポート**:
  - 1025: SMTP（アプリケーションからメール送信）
  - 8025: Web UI（送信メール確認用）
- **用途**: 開発中のメール送信機能のテスト

### 4. MinIOコンテナ（S3互換ストレージ）
- **イメージ**: minio/minio
- **ポート**:
  - 9000: S3 API
  - 9001: Management Console
- **用途**: ファイルアップロード機能の開発・テスト
- **データ永続化**: Docker volume使用

### 5. CDKコンテナ（インフラ管理）
- **技術スタック**: Node.js 20、AWS CDK CLI
- **プロファイル**: cdk（必要時のみ起動）
- **AWS認証情報**: ホストの~/.awsをマウント

## 成果物

### Dockerファイル
- `backend/Dockerfile.dev` - バックエンド開発用Dockerfile
- `cdk/Dockerfile` - CDK用Dockerfile

### 設定ファイル
- `docker-compose.yml` - 全サービスのオーケストレーション
- `backend/pyproject.toml` - Python依存関係定義
- `backend/.env.example` - 環境変数テンプレート
- `backend/.gitignore` - Git除外設定

### FastAPIアプリケーションコード（レイヤードアーキテクチャ）
- `backend/app/main.py` - FastAPIエントリーポイント
- `backend/app/core/config.py` - 設定管理
- `backend/app/core/database.py` - データベース接続
- `backend/app/api/` - APIエンドポイント層
  - `backend/app/api/v1/router.py` - APIルーター
  - `backend/app/api/v1/endpoints/health.py` - ヘルスチェックエンドポイント
  - `backend/app/api/v1/endpoints/examples.py` - サンプルエンドポイント
- `backend/app/domain/` - ドメイン層（エンティティ、バリューオブジェクト）
  - `backend/app/domain/example.py` - サンプルドメインモデル
- `backend/app/infrastructure/` - インフラ層（リポジトリ実装、外部サービス）
  - `backend/app/infrastructure/database/models.py` - SQLAlchemyモデル
  - `backend/app/infrastructure/repositories/example_repository.py` - サンプルリポジトリ
  - `backend/app/infrastructure/email/smtp_client.py` - メール送信クライアント（MailHog）
  - `backend/app/infrastructure/storage/s3_client.py` - S3クライアント（MinIO）
- `backend/app/application/` - アプリケーション層（ユースケース、サービス）
  - `backend/app/application/services/example_service.py` - サンプルサービス
- `backend/app/schemas/` - Pydanticスキーマ
  - `backend/app/schemas/example.py` - サンプルスキーマ

### データベースマイグレーション
- `backend/alembic.ini` - Alembic設定
- `backend/alembic/env.py` - Alembicエントリーポイント
- `backend/alembic/versions/` - マイグレーションファイル格納ディレクトリ

### テストコード
- `backend/tests/conftest.py` - pytestフィクスチャ
- `backend/tests/test_health.py` - ヘルスチェックAPIテスト
- `backend/tests/test_examples.py` - サンプルAPIテスト

### ドキュメント
- `backend/README.md` - バックエンド開発ガイド
- `.steering/20260119-backend-local-env/design.md` - 設計書
- `.steering/20260119-backend-local-env/tasklist.md` - タスクリスト

## 受け入れ条件

### 必須条件
1. `docker-compose up -d`で全サービスが起動すること
2. バックエンドAPIが http://localhost:8000 でアクセス可能
3. PostgreSQLに接続可能であること
4. MailHog Web UIが http://localhost:8025 でアクセス可能
5. MinIO Consoleが http://localhost:9001 でアクセス可能
6. バックエンドのコード変更時にホットリロードが動作すること
7. uvによる依存関係管理が機能すること
8. レイヤードアーキテクチャに基づくディレクトリ構造が構築されていること

### 動作確認項目
1. **API動作確認**: http://localhost:8000/docs でSwagger UIが表示される
2. **ヘルスチェック**: `GET /api/v1/health` が正常応答
3. **データベース接続**: バックエンドからPostgreSQLへの接続成功
4. **メール送信テスト**: バックエンドからMailHogへメール送信し、Web UIで確認
5. **S3操作テスト**: バックエンドからMinIOへファイルアップロード・ダウンロード成功
6. **ホットリロード**: Pythonコード変更時に自動再起動
7. **テスト実行**: `docker-compose exec backend uv run pytest` でテスト成功
8. **マイグレーション**: `docker-compose exec backend uv run alembic upgrade head` が成功

## 制約事項

### 技術的制約
- Python 3.11以上を使用
- PostgreSQL 16-alpineイメージを使用
- uvパッケージマネージャーの使用必須
- docker-compose version 3.8以上
- レイヤードアーキテクチャに準拠（Presentation → Application → Domain → Infrastructure）

### 環境制約
- Docker Desktopがインストール済みであること
- 以下のポートが空いていること:
  - 5432（PostgreSQL）
  - 8000（バックエンドAPI）
  - 8025（MailHog Web UI）
  - 9000（MinIO API）
  - 9001（MinIO Console）
  - 1025（MailHog SMTP）

### セキュリティ制約
- 開発環境用の認証情報のみ使用（本番用は使用禁止）
- .env.localファイルは.gitignoreに追加
- AWS認証情報は読み取り専用でマウント

## 非機能要件

### パフォーマンス
- コンテナ起動時間: 30秒以内
- ホットリロード応答時間: 3秒以内
- uvによる依存関係インストール: pip比で2倍以上高速

### 保守性
- 各コンテナの責務を明確に分離
- 環境変数による設定の外部化
- ログの標準出力への集約
- レイヤードアーキテクチャによる責務分離

### 可用性
- データベースデータの永続化
- MinIOデータの永続化
- コンテナ再起動時のデータ保持

## 除外事項
- フロントエンド環境（別タスクで実装）
- CI/CD設定
- 本番環境へのデプロイ
- SSL/TLS設定（ローカル開発ではHTTPを使用）
- 認証・認可機能の本格実装（サンプル実装は除く）
- 業務ロジックの実装（基本的なCRUDサンプルのみ）

## 参照ドキュメント
- [docs/architecture/local_dev.md](../../docs/architecture/local_dev.md) - ローカル開発環境設計書
- [CLAUDE.md](../../CLAUDE.md) - 開発プロセス定義
