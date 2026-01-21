# バックエンド開発環境ガイド

## バックエンドの立ち上げ方

### 1. Dev Containerで開く
VSCodeで `backend` フォルダを開き、「Dev Containerで再度開く」を選択します。

以下のサービスが自動的に起動します：
- **backend** - FastAPIアプリケーション (ポート8000)
- **postgres** - PostgreSQLデータベース (ポート5432)
- **mailhog** - メール送信テスト用SMTPサーバー (ポート8025)
- **minio** - S3互換オブジェクトストレージ (ポート9000, 9001)

### 2. データベースマイグレーション
初回起動時はマイグレーションを実行してテーブルを作成します：
```bash
uv run alembic upgrade head
```

### 3. アプリケーション起動（デバッグモード）
VSCodeのデバッグ機能を使って起動します：
1. VSCodeのサイドバーで「実行とデバッグ」を開く
2. 「Python: FastAPI」を選択
3. F5キーでデバッグ開始

アクセス：
- API: http://localhost:8000
- API ドキュメント (Swagger UI): http://localhost:8000/docs
- ヘルスチェック: http://localhost:8000/api/v1/health

> **Note:** ホットリロードが有効なので、コードを変更すると自動的に再起動されます。

## Dev Container内でできること

### 1. デバッグ方法

[.vscode/launch.json](backend/.vscode/launch.json) に2つのデバッグ設定があります。

#### FastAPIアプリケーションのデバッグ
1. VSCodeのサイドバーで「実行とデバッグ」を開く
2. 「Python: FastAPI」を選択
3. F5キーでデバッグ開始
4. コード内にブレークポイントを設定（行番号の左をクリック）
5. APIにリクエストを送ると、ブレークポイントで停止

**デバッグ設定の内容：**
- uvicornサーバーをデバッグモードで起動
- ホットリロード有効（`--reload`）
- 環境変数が自動設定（DATABASE_URL, SMTP_HOST, S3_ENDPOINTなど）
- `justMyCode: false` - ライブラリコードもステップ実行可能

**デバッグのヒント：**
- F9: ブレークポイントの設定/解除
- F5: 次のブレークポイントまで実行
- F10: ステップオーバー（次の行へ）
- F11: ステップイン（関数内に入る）
- Shift+F11: ステップアウト（関数から出る）

#### pytestのデバッグ
1. テストファイル内にブレークポイントを設定
2. デバッグパネルで「Python: pytest」を選択
3. F5キーでテストをデバッグ実行

設定内容：
- `-v`: 詳細モード
- `-s`: print文の出力を表示

#### ターミナルから起動する場合
デバッグ機能を使わずに起動したい場合：
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. データベースマイグレーション（Alembic）

#### マイグレーションファイルの作成
モデルを変更したら、新しいマイグレーションファイルを自動生成します：
```bash
uv run alembic revision --autogenerate -m "マイグレーションの説明"
```

例：
```bash
uv run alembic revision --autogenerate -m "add user table"
```

生成されたファイルは [alembic/versions/](backend/alembic/versions/) に保存されます。

#### マイグレーションの適用
```bash
# 最新版まで適用
uv run alembic upgrade head

# 1つ進める
uv run alembic upgrade +1

# 特定のリビジョンまで適用
uv run alembic upgrade <revision_id>
```

#### マイグレーションの巻き戻し
```bash
# 1つ戻す
uv run alembic downgrade -1

# ベースまで戻す（全削除）
uv run alembic downgrade base
```

#### マイグレーション履歴の確認
```bash
# 現在のリビジョンを確認
uv run alembic current

# マイグレーション履歴を表示
uv run alembic history

# 詳細表示
uv run alembic history --verbose
```

#### データベース接続設定
マイグレーションの接続先は [alembic.ini](backend/alembic.ini#L4) で設定されています：
```ini
sqlalchemy.url = postgresql://postgres:postgres@postgres:5432/app_db
```

### 3. ユニットテスト

#### 全テスト実行
```bash
# 全テストを実行
uv run pytest

# 詳細モードで実行
uv run pytest -v

# print文の出力を表示
uv run pytest -s

# カバレッジレポート付き
uv run pytest --cov=app --cov-report=html
```

カバレッジレポートは `htmlcov/index.html` に生成されます。

#### 特定のテストを実行
```bash
# 特定のディレクトリ
uv run pytest tests/unit/

# 特定のファイル
uv run pytest tests/unit/domain/test_example.py

# 特定のテストケース
uv run pytest tests/unit/domain/test_example.py::test_example_creation

# キーワードでフィルタリング
uv run pytest -k "example"
```

#### テスト構成
```
tests/
├── conftest.py              # 共通フィクスチャ
├── unit/                    # ユニットテスト
│   ├── domain/             # ドメイン層のテスト
│   ├── application/        # アプリケーション層のテスト
│   └── mocks/              # モックオブジェクト
└── integration/            # 結合テスト
    ├── conftest.py         # 結合テスト用フィクスチャ
    ├── test_health.py      # ヘルスチェックのテスト
    └── test_examples.py    # APIエンドポイントのテスト
```

#### テストの種類

##### ユニットテスト
モックを使って外部依存を排除したテスト：
- [tests/unit/domain/test_example.py](backend/tests/unit/domain/test_example.py) - エンティティのテスト
- [tests/unit/application/test_example_usecase.py](backend/tests/unit/application/test_example_usecase.py) - ユースケースのテスト

##### 結合テスト
実際のデータベースを使用したテスト：
- [tests/integration/test_health.py](backend/tests/integration/test_health.py) - ヘルスチェックAPI
- [tests/integration/test_examples.py](backend/tests/integration/test_examples.py) - CRUD API

#### テストのベストプラクティス
```bash
# テスト実行前にコードフォーマット
uv run ruff format .

# リンターでチェック
uv run ruff check .

# 型チェック
uv run mypy app/

# すべてのチェックとテストを実行
uv run ruff format . && uv run ruff check . && uv run pytest
```

### 4. その他の便利なコマンド

#### コードフォーマット・リント
```bash
# 自動フォーマット（Ruff）
uv run ruff format .

# リンターでチェック
uv run ruff check .

# 自動修正
uv run ruff check --fix .

# 型チェック（mypy）
uv run mypy app/
```

> **Note:** Dev Containerでは保存時に自動フォーマットが有効になっています（[devcontainer.json](backend/.devcontainer/devcontainer.json#L20) で設定）

#### データベース操作
```bash
# PostgreSQLに直接接続
psql postgresql://postgres:postgres@postgres:5432/app_db

# テーブル一覧
psql postgresql://postgres:postgres@postgres:5432/app_db -c "\dt"

# SQLを実行
psql postgresql://postgres:postgres@postgres:5432/app_db -c "SELECT * FROM examples;"
```

#### MinIO（S3互換ストレージ）
- Web UI: http://localhost:9001
- ユーザー名: `minioadmin`
- パスワード: `minioadmin`

バケットの作成やファイルのアップロード/ダウンロードが可能です。

#### MailHog（メールテスト）
- Web UI: http://localhost:8025
- 送信したメールがここで確認できます

アプリケーションから送信されたメールはすべてMailHogで受信され、実際には送信されません。

## トラブルシューティング

### 依存関係の問題
```bash
# 依存関係を再同期
uv sync

# キャッシュをクリアして再インストール
uv sync --reinstall
```

### データベースのリセット
```bash
# 全テーブルを削除してマイグレーションをやり直す
uv run alembic downgrade base
uv run alembic upgrade head
```

### ポートが使用中のエラー
```bash
# ポート8000を使用しているプロセスを確認
lsof -i :8000

# プロセスを終了
kill -9 <PID>
```

### Dev Containerの再ビルド
1. コマンドパレット（Cmd+Shift+P / Ctrl+Shift+P）を開く
2. 「Dev Containers: Rebuild Container」を選択
3. コンテナが再ビルドされ、依存関係が再インストールされます

## プロジェクト構造

```
backend/
├── app/
│   ├── main.py                    # FastAPIアプリケーションのエントリーポイント
│   ├── core/                      # 設定とデータベース接続
│   ├── domain/                    # ドメイン層（エンティティ）
│   ├── application/               # アプリケーション層（ユースケース）
│   ├── infrastructure/            # インフラ層（リポジトリ、外部サービス）
│   ├── api/                       # API層（エンドポイント）
│   └── schemas/                   # Pydanticスキーマ
├── tests/                         # テストコード
├── alembic/                       # マイグレーションファイル
├── .vscode/                       # VSCode設定（デバッグ設定）
├── .devcontainer/                 # Dev Container設定
├── pyproject.toml                 # プロジェクト設定と依存関係
└── alembic.ini                    # Alembic設定
```

## 参考リンク

- FastAPI公式ドキュメント: https://fastapi.tiangolo.com/
- Alembic公式ドキュメント: https://alembic.sqlalchemy.org/
- pytest公式ドキュメント: https://docs.pytest.org/
- uv公式ドキュメント: https://docs.astral.sh/uv/
