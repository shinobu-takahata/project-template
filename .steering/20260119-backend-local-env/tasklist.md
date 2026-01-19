# バックエンドローカル開発環境構築 - タスクリスト

## タスク概要
バックエンドローカル開発環境の構築を段階的に実装します。
各タスクは独立して検証可能な単位で定義されています。

## フェーズ1: 基盤構築

### タスク1: プロジェクト基本構造の作成
- [ ] `backend/`ディレクトリ作成
- [ ] `backend/.gitignore`作成
- [ ] `backend/pyproject.toml`作成
- [ ] `backend/README.md`作成
- [ ] `backend/.env.example`作成

**完了条件:**
- 必要なディレクトリとファイルが作成されている

### タスク2: Dockerファイルの作成
- [ ] `backend/Dockerfile.dev`作成
- [ ] `cdk/Dockerfile`作成
- [ ] `docker-compose.yml`作成（プロジェクトルート）

**完了条件:**
- Dockerファイルが設計書通りに作成されている

### タスク3: コンテナ起動確認
- [ ] `docker-compose up -d`でコンテナ起動
- [ ] 各サービスの起動確認
  - backend
  - postgres
  - mailhog
  - minio
- [ ] ポート接続確認
  - 8000: バックエンド
  - 5432: PostgreSQL
  - 8025: MailHog Web UI
  - 9000: MinIO API
  - 9001: MinIO Console

**完了条件:**
- 全サービスが正常起動している
- 各ポートにアクセス可能

## フェーズ2: FastAPIアプリケーション基盤

### タスク4: ディレクトリ構造の作成
- [ ] `backend/app/`ディレクトリ構造作成
  - `app/__init__.py`
  - `app/core/`
  - `app/api/v1/endpoints/`
  - `app/application/`
  - `app/domain/`
  - `app/infrastructure/database/`
  - `app/infrastructure/repositories/`
  - `app/infrastructure/email/`
  - `app/infrastructure/storage/`
  - `app/schemas/`
- [ ] `backend/tests/`ディレクトリ構造作成
- [ ] `backend/alembic/`ディレクトリ作成

**完了条件:**
- 全ディレクトリが作成され、各ディレクトリに`__init__.py`が配置されている

### タスク5: コア機能の実装
- [ ] `app/core/config.py`実装（設定管理）
- [ ] `app/core/database.py`実装（DB接続）
- [ ] `app/main.py`実装（FastAPIエントリーポイント）

**完了条件:**
- FastAPIアプリケーションが起動する
- http://localhost:8000/docs でSwagger UIが表示される

### タスク6: ヘルスチェックエンドポイントの実装
- [ ] `app/api/v1/router.py`実装
- [ ] `app/api/v1/endpoints/health.py`実装
- [ ] ヘルスチェックエンドポイントの動作確認

**完了条件:**
- `GET /api/v1/health`が正常応答
- データベース接続確認が動作している

## フェーズ3: レイヤードアーキテクチャ実装

### タスク7: ドメイン層の実装
- [ ] `app/domain/example.py`実装
  - Exampleエンティティ定義
  - ドメインロジック実装

**完了条件:**
- エンティティクラスが定義されている
- ドメインロジックが実装されている

### タスク8: インフラストラクチャ層の実装（データベース）
- [ ] `app/infrastructure/database/models.py`実装
  - ExampleModelの定義
- [ ] `app/infrastructure/repositories/example_repository.py`実装
  - CRUD操作実装
  - エンティティ⇔モデル変換実装

**完了条件:**
- SQLAlchemyモデルが定義されている
- リポジトリクラスが実装されている

### タスク9: アプリケーション層の実装
- [ ] `app/application/example_usecase.py`実装
  - サンプルユースケース実装
  - トランザクション管理

**完了条件:**
- ユースケースクラスが実装されている
- リポジトリとの連携が動作している

### タスク10: プレゼンテーション層の実装
- [ ] `app/schemas/example.py`実装
  - Pydanticスキーマ定義
- [ ] `app/api/v1/endpoints/examples.py`実装
  - CRUD APIエンドポイント実装
- [ ] `app/api/v1/router.py`にルーター登録

**完了条件:**
- APIエンドポイントが実装されている
- Swagger UIで確認可能

## フェーズ4: データベースマイグレーション

### タスク11: Alembic設定
- [ ] `backend/alembic.ini`作成
- [ ] `backend/alembic/env.py`実装
- [ ] `backend/alembic/script.py.mako`配置

**完了条件:**
- Alembic設定が完了している

### タスク12: 初回マイグレーション作成
- [ ] マイグレーションファイル生成
  ```bash
  docker-compose exec backend uv run alembic revision --autogenerate -m "Initial migration"
  ```
- [ ] マイグレーション適用
  ```bash
  docker-compose exec backend uv run alembic upgrade head
  ```
- [ ] データベース確認

**完了条件:**
- マイグレーションが正常に適用されている
- examplesテーブルが作成されている

## フェーズ5: 外部サービス連携

### タスク13: MailHog連携実装
- [ ] `app/infrastructure/email/smtp_client.py`実装
- [ ] メール送信テスト実装
- [ ] MailHog Web UIでメール確認

**完了条件:**
- メール送信機能が実装されている
- MailHogでメールが受信できる

### タスク14: MinIO連携実装
- [ ] `app/infrastructure/storage/s3_client.py`実装
- [ ] MinIOバケット作成（app-bucket）
- [ ] ファイルアップロード/ダウンロードテスト

**完了条件:**
- S3クライアントが実装されている
- MinIOでファイル操作が可能

## フェーズ6: テスト実装

### タスク15: テスト基盤の構築
- [ ] `tests/conftest.py`実装
  - テスト用DBフィクスチャ
  - TestClientフィクスチャ
- [ ] `tests/test_health.py`実装

**完了条件:**
- テストフィクスチャが動作している
- ヘルスチェックテストが成功

### タスク16: 統合テストの実装
- [ ] `tests/test_examples.py`実装
  - 作成テスト
  - 取得テスト
  - 一覧テスト
- [ ] テスト実行確認
  ```bash
  docker-compose exec backend uv run pytest
  ```

**完了条件:**
- 全テストがパスしている
- カバレッジレポートが生成される

## フェーズ7: 動作確認・ドキュメント

### タスク17: エンドツーエンド動作確認
- [ ] コンテナ再起動テスト
  ```bash
  docker-compose down
  docker-compose up -d
  ```
- [ ] データ永続性確認
- [ ] ホットリロード確認
- [ ] 各APIエンドポイント動作確認
  - POST /api/v1/examples/
  - GET /api/v1/examples/{id}
  - GET /api/v1/examples/

**完了条件:**
- 全機能が正常動作している
- データが永続化されている

### タスク18: README.md作成
- [ ] `backend/README.md`作成
  - セットアップ手順
  - 開発ワークフロー
  - テスト実行方法
  - トラブルシューティング

**完了条件:**
- READMEに必要な情報が記載されている
- 第三者がセットアップ可能

### タスク19: 最終検証
- [ ] 受け入れ条件の確認
  - [ ] `docker-compose up -d`で全サービス起動
  - [ ] http://localhost:8000 でAPIアクセス可能
  - [ ] http://localhost:8000/docs でSwagger UI表示
  - [ ] http://localhost:8025 でMailHog Web UI表示
  - [ ] http://localhost:9001 でMinIO Console表示
  - [ ] PostgreSQL接続確認
  - [ ] ホットリロード動作確認
  - [ ] uv依存関係管理動作確認
  - [ ] レイヤードアーキテクチャ構造確認
- [ ] 動作確認項目のチェック
  - [ ] ヘルスチェックAPI成功
  - [ ] データベース接続成功
  - [ ] メール送信テスト成功
  - [ ] S3操作テスト成功
  - [ ] テスト実行成功
  - [ ] マイグレーション成功

**完了条件:**
- 全受け入れ条件を満たしている
- 全動作確認項目がパスしている

## タスク実行順序
```
Phase 1: 基盤構築
  Task 1 → Task 2 → Task 3

Phase 2: FastAPI基盤
  Task 4 → Task 5 → Task 6

Phase 3: レイヤードアーキテクチャ
  Task 7 → Task 8 → Task 9 → Task 10

Phase 4: データベースマイグレーション
  Task 11 → Task 12

Phase 5: 外部サービス連携
  Task 13, Task 14 (並行可能)

Phase 6: テスト
  Task 15 → Task 16

Phase 7: 動作確認・ドキュメント
  Task 17 → Task 18 → Task 19
```

## 進捗管理
- [ ] Phase 1: 基盤構築
- [ ] Phase 2: FastAPI基盤
- [ ] Phase 3: レイヤードアーキテクチャ
- [ ] Phase 4: データベースマイグレーション
- [ ] Phase 5: 外部サービス連携
- [ ] Phase 6: テスト
- [ ] Phase 7: 動作確認・ドキュメント

## 備考
- 各タスク完了後、動作確認を実施すること
- 問題が発生した場合は、前のタスクに戻って原因を特定すること
- コミットは各フェーズ完了時に実施すること
