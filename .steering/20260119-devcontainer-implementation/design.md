# DevContainer実装 - 設計

## 概要
バックエンド開発向けのDev Container環境を構築します。既存のdocker-compose.ymlと統合し、VSCodeでシームレスに開発できる環境を提供します。

## アーキテクチャ

### 全体構成
```
┌─────────────────────────────────────────────────┐
│ VSCode (Host)                                   │
│  - Dev Containers拡張機能                        │
└─────────────────────────────────────────────────┘
           ↓ Remote接続
┌─────────────────────────────────────────────────┐
│ Dev Container (backend)                         │
│  - Python 3.11 + uv                            │
│  - VSCode Server                                │
│  - Python拡張機能 (自動インストール)              │
│  - Ruff, mypy, pytest                          │
│  - /workspace (volumeマウント)                  │
│  - /workspace/.venv (Dockerfile.devで作成)      │
└─────────────────────────────────────────────────┘
           ↓ ネットワーク接続
┌─────────────────────────────────────────────────┐
│ docker-compose services                         │
│  - postgres (Port: 5432)                       │
│  - mailhog (Port: 1025, 8025)                  │
│  - minio (Port: 9000, 9001)                    │
└─────────────────────────────────────────────────┘
```

### ネットワーク構成
- Dev Containerは既存のdocker-composeネットワークに参加
- サービス名で他のコンテナにアクセス可能
  - `postgres:5432`
  - `mailhog:1025`
  - `minio:9000`

## 実装アプローチ

### 方針: 既存のdocker-compose.ymlを最大限活用

**重要な前提:**
- 既存のDockerfile.devは`RUN uv sync`でコンテナ内に`.venv`を作成
- ホストには`.venv`を作らない（設計通り）
- Dev Containerでもコンテナ内の`.venv`を使用

**結論:**
- docker-compose.dev.ymlは**不要**
- 既存のdocker-compose.ymlをそのまま使用
- devcontainer.jsonで必要な設定を追加

### 1. Dev Container設定ファイル

#### ディレクトリ構造
```
backend/
├── .devcontainer/
│   └── devcontainer.json        # Dev Container設定
├── .vscode/
│   ├── launch.json              # デバッグ設定
│   ├── settings.json            # VSCode設定
│   └── extensions.json          # 推奨拡張機能
├── Dockerfile.dev               # 既存（変更なし）
├── pyproject.toml
└── app/
```

### 2. devcontainer.json設計

```json
{
  "name": "Backend (FastAPI)",

  // 既存のdocker-compose.ymlを使用
  "dockerComposeFile": "../../docker-compose.yml",
  "service": "backend",
  "workspaceFolder": "/app",

  // バックエンドと依存サービスを起動
  "runServices": ["backend", "postgres", "mailhog", "minio"],

  // コンテナのCMDを上書き（sleep infinityにしてVSCodeが制御）
  "overrideCommand": true,

  // VSCode拡張機能の自動インストール
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "charliermarsh.ruff",
        "ms-python.debugpy"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/app/.venv/bin/python",
        "python.linting.enabled": true,
        "python.linting.ruffEnabled": true,
        "python.formatting.provider": "none",
        "[python]": {
          "editor.defaultFormatter": "charliermarsh.ruff",
          "editor.formatOnSave": true,
          "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit"
          }
        },
        "ruff.path": ["/app/.venv/bin/ruff"],
        "python.testing.pytestEnabled": true,
        "python.testing.unittestEnabled": false,
        "python.testing.pytestArgs": ["tests"]
      }
    }
  },

  // ポートフォワーディング
  "forwardPorts": [8000, 5432, 8025, 9000, 9001],
  "portsAttributes": {
    "8000": {
      "label": "FastAPI",
      "onAutoForward": "notify"
    },
    "5432": {
      "label": "PostgreSQL"
    },
    "8025": {
      "label": "MailHog Web UI"
    },
    "9000": {
      "label": "MinIO API"
    },
    "9001": {
      "label": "MinIO Console"
    }
  },

  // コンテナ作成後のコマンド（依存関係の同期）
  "postCreateCommand": "uv sync",

  // Git認証情報の共有
  "mounts": [
    "source=${localEnv:HOME}/.gitconfig,target=/root/.gitconfig,type=bind,consistency=cached"
  ],

  // 環境変数
  "remoteEnv": {
    "PYTHONUNBUFFERED": "1",
    "ENV": "development"
  }
}
```

### 3. VSCode設定

#### .vscode/launch.json（デバッグ設定）

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
      ],
      "jinja": true,
      "justMyCode": false,
      "env": {
        "PYTHONUNBUFFERED": "1",
        "DATABASE_URL": "postgresql://postgres:postgres@postgres:5432/app_db",
        "ENV": "development",
        "SMTP_HOST": "mailhog",
        "SMTP_PORT": "1025",
        "S3_ENDPOINT": "http://minio:9000",
        "S3_ACCESS_KEY": "minioadmin",
        "S3_SECRET_KEY": "minioadmin",
        "S3_BUCKET": "app-bucket"
      },
      "console": "integratedTerminal"
    },
    {
      "name": "Python: pytest",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": [
        "-v",
        "-s"
      ],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

#### .vscode/settings.json（ワークスペース設定）

```json
{
  "python.defaultInterpreterPath": "/app/.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "ruff.path": ["/app/.venv/bin/ruff"],
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  },
  "files.watcherExclude": {
    "**/.venv/**": true
  }
}
```

#### .vscode/extensions.json（推奨拡張機能）

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "ms-python.debugpy",
    "ms-vscode-remote.remote-containers"
  ]
}
```

### 4. Dockerfile.devの確認

既存のDockerfile.devはそのまま使用可能です。

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# uvインストール（pip経由）
RUN pip install --no-cache-dir uv

# 依存関係ファイルコピー
COPY pyproject.toml ./

# 依存関係インストール
RUN uv sync

# アプリケーションコードはvolume経由でマウント

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Dev Containerでの挙動:**
1. `overrideCommand: true`により、CMDは実行されない
2. コンテナは起動したまま待機
3. VSCodeがコンテナに接続
4. 開発者がF5でデバッガ起動、またはターミナルでコマンド実行

## 依存サービスとの接続

### PostgreSQL
```python
# app/core/config.py
DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/app_db"
```

### MailHog
```python
# app/infrastructure/external/email.py
SMTP_HOST = "mailhog"
SMTP_PORT = 1025
```

### MinIO
```python
# app/infrastructure/external/s3.py
S3_ENDPOINT = "http://minio:9000"
```

すべてサービス名でアクセス可能（docker-composeのネットワーク内）

## 開発ワークフロー

### 1. Dev Container起動

**初回:**
1. VSCodeでbackendフォルダを開く
2. 右下に表示される通知「Reopen in Container」をクリック
3. Dev Containerが自動的にビルド・起動
4. 依存サービス（postgres、mailhog、minio）も自動起動
5. `postCreateCommand`で`uv sync`実行
6. VSCode拡張機能が自動インストール

**2回目以降:**
1. VSCodeでbackendフォルダを開く
2. 自動的にDev Containerで起動

### 2. 開発

**コード編集:**
- VSCodeで通常通り編集
- 保存時に自動フォーマット（Ruff）

**デバッグ:**
- F5キーでFastAPIアプリを起動・デバッグ
- ブレークポイントで停止
- 変数の確認、ステップ実行が可能

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

### 3. 既存フローとの互換性

Dev Containerを使わない開発者は、従来通り開発可能:

```bash
# 従来の方法
docker-compose up -d
# VSCodeでbackendフォルダを開いて編集
# docker-compose exec backend uv run pytest
```

## パフォーマンス

### ファイルマウント

```yaml
# docker-compose.yml（既存）
volumes:
  - ./backend:/app
```

**特徴:**
- ホストのbackendフォルダがコンテナの`/app`にマウント
- `.venv`はコンテナ内に作成（Dockerfile.devで`RUN uv sync`）
- ホストと同期されるのはソースコードのみ

**パフォーマンス:**
- ソースコードの読み書き: ホストと同期（若干遅延あり）
- `.venv`の読み書き: コンテナ内部（高速）

**結論**: 特別な最適化は不要

### ホットリロード

uvicornの`--reload`オプションでファイル変更を検知:
- ファイル監視対象: `/app/app/**/*.py`
- 変更検知後、自動的に再読み込み

## セキュリティ考慮事項

### 1. Git認証情報
- ホストの`.gitconfig`をマウント
- SSH鍵は自動的に共有される（Dev Containers機能）

### 2. 環境変数
- 機密情報は`.env.local`に記載（.gitignore済み）
- docker-compose.ymlの環境変数を使用

## トラブルシューティング対策

### 1. ポート競合
- Dev Containerのポート8000がホストで使用中の場合、自動的に別ポートにマッピング
- VSCodeが通知で新しいポートを表示

### 2. 依存関係の不整合
```bash
# コンテナ内で実行
uv sync --reinstall
```

### 3. コンテナ再ビルド
```bash
# VSCodeコマンドパレット（Cmd/Ctrl + Shift + P）
Dev Containers: Rebuild Container
```

### 4. ログ確認
```bash
# docker-composeのログ
docker-compose logs -f backend
docker-compose logs -f postgres
```

## 変更ファイル一覧

### 新規作成
1. `backend/.devcontainer/devcontainer.json`
2. `backend/.vscode/launch.json`
3. `backend/.vscode/settings.json`
4. `backend/.vscode/extensions.json`

### 変更
なし（既存ファイルはすべてそのまま使用）

### 削除
- `backend/.venv/`（ホスト側に誤って作成されたもの）

## 後方互換性

### 従来の開発フロー（docker-compose）
```bash
# 従来通り動作
docker-compose up -d
cd frontend
npm run dev
```

### Dev Container使用
```bash
# VSCodeでbackendフォルダを開く → 自動的にDev Containerで起動
cd frontend  # ホスト側で実行
npm run dev
```

両方のワークフローが共存可能。

## 実装優先度

### Phase 1: 最小構成（MVP）
1. `backend/.devcontainer/devcontainer.json`の作成
2. VSCode拡張機能の自動インストール設定
3. 動作確認（Dev Containerで起動）

### Phase 2: 開発体験向上
1. デバッグ設定（`backend/.vscode/launch.json`）
2. VSCodeワークスペース設定（`backend/.vscode/settings.json`）
3. 推奨拡張機能リスト（`backend/.vscode/extensions.json`）

### Phase 3: ドキュメント整備
1. backend/README.mdへのDev Container使用手順追記
2. トラブルシューティングガイド作成

## 期待される改善

### Before（現状）
```
開発者がbackendを編集
→ VSCodeで編集、Lintは手動
→ docker-compose exec backend uv run pytest
→ デバッグはprintデバッグ
```

### After（Dev Container）
```
開発者がbackendを編集
→ VSCodeで編集、保存時に自動フォーマット・Lint
→ VSCodeのTest Explorerでテスト実行
→ F5キーでデバッガ起動、ブレークポイントで停止
→ すべてコンテナ内で完結
```

## 参考資料
- [Dev Containers Specification](https://containers.dev/)
- [VSCode Dev Containers - Docker Compose](https://code.visualstudio.com/docs/devcontainers/docker-compose)
- [Python in Dev Containers](https://code.visualstudio.com/docs/devcontainers/tutorial)
