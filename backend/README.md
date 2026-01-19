# Backend API

FastAPIを使用したバックエンドアプリケーション

## 技術スタック

- **Python**: 3.11
- **フレームワーク**: FastAPI
- **ORM**: SQLAlchemy
- **マイグレーション**: Alembic
- **パッケージマネージャー**: uv
- **リンター/フォーマッター**: Ruff
- **テスト**: pytest

## セットアップ

### 前提条件

- Docker Desktop
- docker-compose

### 開発方法の選択

本プロジェクトでは2つの開発方法をサポートしています:

1. **Dev Container（推奨）**: VSCodeでコンテナ内開発
2. **docker-compose**: 従来の方法

---

## Dev Container（推奨）

### 必要な環境
- Docker Desktop
- VSCode
- Dev Containers拡張機能（`ms-vscode-remote.remote-containers`）

### 起動方法

1. **VSCodeでbackendフォルダを開く**
```bash
code backend/
```

2. **右下の通知「Reopen in Container」をクリック**
   - Dev Containerが自動的にビルド・起動
   - 依存サービス（postgres、mailhog、minio）も自動起動
   - VSCode拡張機能が自動インストール
   - `uv sync`が自動実行

3. **開発開始**
   - コンテナ内で開発環境が完全にセットアップされています

### 開発

**FastAPIアプリの起動:**
- `F5`キーを押す
- デバッグ設定「Python: FastAPI」が自動実行
- http://localhost:8000 でアクセス可能

**コード編集:**
- 保存時に自動フォーマット（Ruff）
- リアルタイムLint表示

**テスト実行:**
```bash
# ターミナルで実行
uv run pytest

# またはVSCodeのTest Explorerから実行
```

**データベースマイグレーション:**
```bash
uv run alembic upgrade head
```

**デバッグ:**
- ブレークポイントを設定
- `F5`でデバッグ起動
- ステップ実行、変数確認が可能

### トラブルシューティング

**コンテナ再ビルド:**
1. コマンドパレット（`Cmd/Ctrl + Shift + P`）を開く
2. `Dev Containers: Rebuild Container`を選択

**依存関係の再インストール:**
```bash
uv sync --reinstall
```

**ログ確認:**
```bash
# docker-composeのログ
docker-compose logs -f backend
docker-compose logs -f postgres
```

---

## docker-compose（従来の方法）

### 初回起動

1. すべてのサービスを起動:
```bash
docker-compose up -d
```

2. データベースマイグレーション:
```bash
docker-compose exec backend uv run alembic upgrade head
```

3. APIドキュメント確認:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 開発ワークフロー

### サービス起動
```bash
docker-compose up -d
```

### ログ確認
```bash
# すべてのサービス
docker-compose logs -f

# バックエンドのみ
docker-compose logs -f backend
```

### 依存関係管理

```bash
# コンテナに入る
docker-compose exec backend sh

# 依存関係追加
uv add <package-name>

# 開発依存関係追加
uv add --dev <package-name>

# 依存関係同期
uv sync

# 依存関係更新
uv lock --upgrade && uv sync
```

### データベースマイグレーション

```bash
# マイグレーションファイル生成
docker-compose exec backend uv run alembic revision --autogenerate -m "description"

# マイグレーション適用
docker-compose exec backend uv run alembic upgrade head

# ロールバック
docker-compose exec backend uv run alembic downgrade -1

# 履歴確認
docker-compose exec backend uv run alembic history
```

### テスト実行

```bash
# すべてのテスト実行
docker-compose exec backend uv run pytest

# カバレッジ付き
docker-compose exec backend uv run pytest --cov=app --cov-report=html

# 特定のテストファイル実行
docker-compose exec backend uv run pytest tests/test_examples.py

# 特定のテスト関数実行
docker-compose exec backend uv run pytest tests/test_examples.py::test_create_example
```

### コード品質管理

```bash
# コンテナに入る
docker-compose exec backend sh

# フォーマット
uv run ruff format .

# リント
uv run ruff check .

# リント（自動修正）
uv run ruff check --fix .

# 型チェック
uv run mypy app/
```

## プロジェクト構造

```
backend/
├── app/
│   ├── main.py                    # FastAPIエントリーポイント
│   ├── core/
│   │   ├── config.py              # 設定管理
│   │   └── database.py            # データベース接続
│   ├── api/
│   │   └── v1/
│   │       ├── router.py          # APIルーター統合
│   │       └── endpoints/         # エンドポイント
│   ├── application/               # ユースケース層
│   ├── domain/                    # ドメイン層
│   ├── infrastructure/            # インフラ層
│   │   ├── database/              # データベース
│   │   ├── repositories/          # リポジトリ
│   │   ├── email/                 # メール送信
│   │   └── storage/               # ストレージ
│   └── schemas/                   # Pydanticスキーマ
├── alembic/                       # マイグレーション
├── tests/                         # テスト
├── Dockerfile.dev                 # 開発用Dockerfile
├── pyproject.toml                 # 依存関係定義
└── README.md
```

## レイヤードアーキテクチャ

本プロジェクトはレイヤードアーキテクチャを採用しています。

### Presentation Layer (api/)
- FastAPIエンドポイント
- リクエスト/レスポンス処理
- バリデーション

### Application Layer (application/)
- ユースケース実装
- ビジネスロジックオーケストレーション
- トランザクション管理

### Domain Layer (domain/)
- エンティティ
- バリューオブジェクト
- ドメインロジック

### Infrastructure Layer (infrastructure/)
- リポジトリ実装
- 外部サービス連携
- データベースアクセス

## 環境変数

`.env.example`を参照してください。

主な環境変数:
- `DATABASE_URL`: PostgreSQL接続URL
- `SMTP_HOST`, `SMTP_PORT`: メール送信設定（MailHog）
- `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`: S3設定（MinIO）

## トラブルシューティング

### コンテナが起動しない

```bash
# ログ確認
docker-compose logs backend

# コンテナ再ビルド
docker-compose build --no-cache backend
docker-compose up -d
```

### データベース接続エラー

```bash
# PostgreSQL状態確認
docker-compose ps postgres

# 接続テスト
docker-compose exec postgres psql -U postgres -d app_db -c "SELECT 1;"
```

### ホットリロードが動作しない

```bash
# コンテナ再起動
docker-compose restart backend

# ログでエラー確認
docker-compose logs -f backend
```

### データベースリセット

```bash
# すべてのコンテナとボリュームを削除
docker-compose down -v

# 再起動
docker-compose up -d

# マイグレーション適用
docker-compose exec backend uv run alembic upgrade head
```

## 外部サービス

### MailHog（メールテスト）
- Web UI: http://localhost:8025
- SMTP: localhost:1025

### MinIO（S3互換ストレージ）
- Console: http://localhost:9001
- API: http://localhost:9000
- 認証情報: minioadmin / minioadmin

## API仕様

起動後、以下のURLでAPI仕様を確認できます:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
