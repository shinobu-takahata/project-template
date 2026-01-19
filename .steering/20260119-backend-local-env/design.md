# バックエンドローカル開発環境構築 - 設計書

## 概要
本ドキュメントは、バックエンドローカル開発環境の詳細設計を定義します。
Docker、docker-compose、uvを用いた高速な開発環境と、レイヤードアーキテクチャに基づくFastAPIアプリケーションの実装アプローチを示します。

## アーキテクチャ設計

### システム構成図
```
┌─────────────────────────────────────────────────┐
│ Docker Compose                                  │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │ Backend (FastAPI) - Port: 8000           │  │
│  │  - Python 3.11 + uv                      │  │
│  │  - uvicorn --reload                      │  │
│  │  - Volume: ./backend:/app                │  │
│  └───────────────────────────────────────────┘  │
│           ↓ connects to                        │
│  ┌───────────────────────────────────────────┐  │
│  │ PostgreSQL - Port: 5432                  │  │
│  │  - postgres:16-alpine                    │  │
│  │  - Volume: postgres_data                 │  │
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
│  │  - Volume: minio_data                    │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │ CDK (インフラ管理) - profile: cdk        │  │
│  │  - Node.js 20 + AWS CDK CLI              │  │
│  │  - Volume: ~/.aws (read-only)            │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### レイヤードアーキテクチャ設計

```
┌──────────────────────────────────────────┐
│         Presentation Layer               │
│    (app/api/v1/endpoints/*.py)          │
│  - FastAPIエンドポイント                  │
│  - リクエスト/レスポンス処理               │
│  - バリデーション（Pydanticスキーマ）      │
└──────────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────┐
│        Application Layer                 │
│      (app/application/*.py)             │
│  - ユースケース実装                       │
│  - ビジネスロジックオーケストレーション      │
│  - トランザクション管理                   │
└──────────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────┐
│          Domain Layer                    │
│       (app/domain/*.py)                 │
│  - エンティティ                          │
│  - バリューオブジェクト                   │
│  - ドメインロジック                       │
└──────────────────────────────────────────┘
                  ↓
┌──────────────────────────────────────────┐
│       Infrastructure Layer               │
│    (app/infrastructure/*/*.py)          │
│  - リポジトリ実装（SQLAlchemy）           │
│  - 外部サービス連携（SMTP、S3）          │
│  - データベース接続                       │
└──────────────────────────────────────────┘
```

## ディレクトリ構造設計

### プロジェクト全体
```
project-template/
├── backend/
│   ├── Dockerfile.dev
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── alembic.ini
│   ├── .env.example
│   ├── .gitignore
│   ├── README.md
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPIエントリーポイント
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # 設定管理
│   │   │   └── database.py            # DB接続管理
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py          # APIルーター統合
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           ├── health.py      # ヘルスチェック
│   │   │           └── examples.py    # サンプルCRUD
│   │   ├── application/
│   │   │   ├── __init__.py
│   │   │   └── example_usecase.py     # サンプルユースケース
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   └── example.py             # サンプルエンティティ
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── database/
│   │   │   │   ├── __init__.py
│   │   │   │   └── models.py          # SQLAlchemyモデル
│   │   │   ├── repositories/
│   │   │   │   ├── __init__.py
│   │   │   │   └── example_repository.py
│   │   │   ├── email/
│   │   │   │   ├── __init__.py
│   │   │   │   └── smtp_client.py     # MailHog連携
│   │   │   └── storage/
│   │   │       ├── __init__.py
│   │   │       └── s3_client.py       # MinIO連携
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── example.py             # Pydanticスキーマ
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_health.py
│       └── test_examples.py
├── cdk/
│   ├── Dockerfile
│   ├── package.json
│   └── (CDK関連ファイル)
└── docker-compose.yml
```

## コンポーネント設計

### 1. Dockerコンテナ設計

#### backend/Dockerfile.dev
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# uvインストール（公式推奨方法）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 依存関係ファイルコピー
COPY pyproject.toml uv.lock ./

# 依存関係インストール
RUN uv sync --frozen

# アプリケーションコードはvolume経由でマウント

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**設計ポイント:**
- マルチステージビルドでuvバイナリを取得
- `--frozen`で再現性のある環境構築
- `--reload`で開発時のホットリロード有効化
- アプリケーションコードはvolumeマウントで高速な開発サイクル

#### cdk/Dockerfile
```dockerfile
FROM node:20-alpine

WORKDIR /cdk

# AWS CDK CLIグローバルインストール
RUN npm install -g aws-cdk

# 依存関係インストール用の準備
COPY package*.json ./
RUN npm install

CMD ["sh"]
```

### 2. docker-compose.yml設計

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
      - SMTP_HOST=mailhog
      - SMTP_PORT=1025
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

**設計ポイント:**
- サービス間の依存関係を`depends_on`で定義
- 環境変数でサービス間の接続設定
- データ永続化用のnamed volume使用
- CDKはprofileで分離（通常起動時は起動しない）

### 3. Python依存関係設計（pyproject.toml）

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
    "boto3>=1.34.0",
    "aiosmtplib>=3.0.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.4",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.26.0",
    "ruff>=0.1.14",
    "mypy>=1.8.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**設計ポイント:**
- FastAPI周辺ライブラリの統合
- 開発依存関係とプロダクション依存関係の分離
- Ruffによる高速リント・フォーマット
- pytestの非同期テスト対応

### 4. FastAPIアプリケーション設計

#### app/main.py（エントリーポイント）
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS設定（開発環境）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーター登録
app.include_router(api_router, prefix=settings.API_V1_STR)
```

#### app/core/config.py（設定管理）
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Backend API"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # SMTP (MailHog)
    SMTP_HOST: str = "mailhog"
    SMTP_PORT: int = 1025

    # S3 (MinIO)
    S3_ENDPOINT: str = "http://minio:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "app-bucket"

    # Environment
    ENV: str = "development"

    class Config:
        case_sensitive = True

settings = Settings()
```

#### app/core/database.py（データベース接続）
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### app/api/v1/router.py（APIルーター統合）
```python
from fastapi import APIRouter

from app.api.v1.endpoints import health, examples

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(examples.router, prefix="/examples", tags=["examples"])
```

#### app/api/v1/endpoints/health.py（ヘルスチェック）
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """ヘルスチェックエンドポイント"""
    # データベース接続確認
    db.execute("SELECT 1")
    return {
        "status": "healthy",
        "database": "connected"
    }
```

#### app/domain/example.py（ドメインエンティティ）
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Example:
    """サンプルエンティティ"""
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    def update_name(self, new_name: str) -> None:
        """名前を更新"""
        if not new_name or len(new_name.strip()) == 0:
            raise ValueError("Name cannot be empty")
        self.name = new_name
        self.updated_at = datetime.utcnow()
```

#### app/infrastructure/database/models.py（SQLAlchemyモデル）
```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.core.database import Base

class ExampleModel(Base):
    __tablename__ = "examples"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

#### app/infrastructure/repositories/example_repository.py
```python
from sqlalchemy.orm import Session

from app.domain.example import Example
from app.infrastructure.database.models import ExampleModel

class ExampleRepository:
    """サンプルリポジトリ"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, example_id: int) -> Example | None:
        """IDでエンティティを取得"""
        model = self.db.query(ExampleModel).filter(ExampleModel.id == example_id).first()
        if model is None:
            return None
        return self._to_entity(model)

    def find_all(self) -> list[Example]:
        """全エンティティを取得"""
        models = self.db.query(ExampleModel).all()
        return [self._to_entity(m) for m in models]

    def save(self, example: Example) -> Example:
        """エンティティを保存"""
        model = ExampleModel(
            name=example.name,
            description=example.description,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def _to_entity(self, model: ExampleModel) -> Example:
        """モデルをエンティティに変換"""
        return Example(
            id=model.id,
            name=model.name,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
```

#### app/application/example_usecase.py
```python
from sqlalchemy.orm import Session

from app.domain.example import Example
from app.infrastructure.repositories.example_repository import ExampleRepository
from app.schemas.example import ExampleCreate

class ExampleUseCase:
    """サンプルユースケース"""

    def __init__(self, db: Session):
        self.repository = ExampleRepository(db)

    def create_example(self, data: ExampleCreate) -> Example:
        """サンプル作成"""
        # ドメインエンティティ生成は簡略化
        from datetime import datetime
        example = Example(
            id=0,  # DBで自動採番
            name=data.name,
            description=data.description,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return self.repository.save(example)

    def get_example(self, example_id: int) -> Example | None:
        """サンプル取得"""
        return self.repository.find_by_id(example_id)

    def list_examples(self) -> list[Example]:
        """サンプル一覧"""
        return self.repository.find_all()
```

#### app/schemas/example.py（Pydanticスキーマ）
```python
from datetime import datetime
from pydantic import BaseModel

class ExampleBase(BaseModel):
    name: str
    description: str | None = None

class ExampleCreate(ExampleBase):
    pass

class ExampleResponse(ExampleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

#### app/api/v1/endpoints/examples.py
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.application.example_usecase import ExampleUseCase
from app.schemas.example import ExampleCreate, ExampleResponse

router = APIRouter()

@router.post("/", response_model=ExampleResponse, status_code=201)
async def create_example(
    data: ExampleCreate,
    db: Session = Depends(get_db)
):
    """サンプル作成"""
    usecase = ExampleUseCase(db)
    example = usecase.create_example(data)
    return example

@router.get("/{example_id}", response_model=ExampleResponse)
async def get_example(
    example_id: int,
    db: Session = Depends(get_db)
):
    """サンプル取得"""
    usecase = ExampleUseCase(db)
    example = usecase.get_example(example_id)
    if example is None:
        raise HTTPException(status_code=404, detail="Example not found")
    return example

@router.get("/", response_model=list[ExampleResponse])
async def list_examples(db: Session = Depends(get_db)):
    """サンプル一覧"""
    usecase = ExampleUseCase(db)
    examples = usecase.list_examples()
    return examples
```

#### app/infrastructure/email/smtp_client.py（MailHog連携）
```python
import aiosmtplib
from email.message import EmailMessage

from app.core.config import settings

class SMTPClient:
    """SMTP送信クライアント（MailHog用）"""

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str = "noreply@example.com"
    ) -> None:
        """メール送信"""
        message = EmailMessage()
        message["From"] = from_email
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
        )
```

#### app/infrastructure/storage/s3_client.py（MinIO連携）
```python
import boto3
from botocore.client import Config

from app.core.config import settings

class S3Client:
    """S3クライアント（MinIO用）"""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        self.bucket = settings.S3_BUCKET

    def upload_file(self, file_path: str, object_name: str) -> None:
        """ファイルアップロード"""
        self.client.upload_file(file_path, self.bucket, object_name)

    def download_file(self, object_name: str, file_path: str) -> None:
        """ファイルダウンロード"""
        self.client.download_file(self.bucket, object_name, file_path)

    def list_objects(self) -> list[str]:
        """オブジェクト一覧"""
        response = self.client.list_objects_v2(Bucket=self.bucket)
        return [obj["Key"] for obj in response.get("Contents", [])]
```

### 5. Alembic設定設計

#### alembic.ini
```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql://postgres:postgres@postgres:5432/app_db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

#### alembic/env.py
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.core.database import Base
from app.infrastructure.database.models import *  # モデルインポート

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 6. テスト設計

#### tests/conftest.py
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db

# テスト用インメモリDB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

#### tests/test_health.py
```python
def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

#### tests/test_examples.py
```python
def test_create_example(client):
    response = client.post(
        "/api/v1/examples/",
        json={"name": "Test Example", "description": "Test Description"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Example"
    assert data["description"] == "Test Description"
    assert "id" in data

def test_get_example(client):
    # 作成
    create_response = client.post(
        "/api/v1/examples/",
        json={"name": "Test Example"}
    )
    example_id = create_response.json()["id"]

    # 取得
    response = client.get(f"/api/v1/examples/{example_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Example"

def test_list_examples(client):
    # 複数作成
    client.post("/api/v1/examples/", json={"name": "Example 1"})
    client.post("/api/v1/examples/", json={"name": "Example 2"})

    # 一覧取得
    response = client.get("/api/v1/examples/")
    assert response.status_code == 200
    assert len(response.json()) == 2
```

## データフロー設計

### CRUDリクエストフロー
```
1. HTTPリクエスト受信
   ↓
2. Presentation Layer (endpoints/examples.py)
   - リクエストバリデーション（Pydanticスキーマ）
   - 依存性注入（DBセッション）
   ↓
3. Application Layer (example_usecase.py)
   - ビジネスロジック実行
   - トランザクション管理
   ↓
4. Domain Layer (domain/example.py)
   - ドメインロジック適用
   - ビジネスルール検証
   ↓
5. Infrastructure Layer (repositories/example_repository.py)
   - データベースアクセス
   - エンティティ⇔モデル変換
   ↓
6. レスポンス返却
   - エンティティ → Pydanticスキーマ変換
   - JSON形式でクライアントに返却
```

## セキュリティ設計

### 環境変数管理
- 開発環境の認証情報のみ使用
- `.env.example`をテンプレートとして提供
- `.env.local`は.gitignoreに追加

### データベース
- 開発用の固定認証情報（postgres/postgres）
- ローカルネットワーク内でのみアクセス可能

### 外部サービス
- MailHog: 認証なし（開発専用）
- MinIO: 開発用固定認証情報（minioadmin/minioadmin）

## パフォーマンス設計

### コンテナ起動最適化
- マルチステージビルドで依存関係レイヤーをキャッシュ
- `uv sync --frozen`で高速な依存関係インストール

### 開発体験最適化
- ホットリロード有効化（uvicorn --reload）
- volumeマウントでコンテナ再ビルド不要
- uvによる高速パッケージ管理

## エラーハンドリング設計

### データベース接続エラー
- ヘルスチェックエンドポイントで検出
- 適切なHTTPステータスコード返却

### バリデーションエラー
- Pydanticによる自動バリデーション
- 422 Unprocessable Entityで詳細エラー返却

### ドメインロジックエラー
- カスタム例外クラス定義
- 適切なHTTPステータスコードにマッピング

## 拡張性設計

### 新規エンドポイント追加
1. `app/schemas/`にPydanticスキーマ追加
2. `app/domain/`にエンティティ追加
3. `app/infrastructure/database/models.py`にモデル追加
4. `app/infrastructure/repositories/`にリポジトリ追加
5. `app/application/`にユースケース追加
6. `app/api/v1/endpoints/`にエンドポイント追加
7. `app/api/v1/router.py`にルーター登録

### 新規外部サービス連携
1. `app/infrastructure/`配下に新規ディレクトリ作成
2. クライアントクラス実装
3. `app/core/config.py`に設定追加
4. docker-compose.ymlにサービス追加（必要に応じて）

## テスト戦略

### 単体テスト
- 各レイヤーごとにテスト
- モック/スタブによる依存関係分離

### 統合テスト
- TestClientによるエンドツーエンドテスト
- インメモリDBでのテスト実行

### カバレッジ目標
- 全体: 80%以上
- ドメイン層: 90%以上

## 参照ドキュメント
- [docs/architecture/local_dev.md](../../docs/architecture/local_dev.md) - ローカル開発環境設計書
- [requirements.md](./requirements.md) - 要求仕様
