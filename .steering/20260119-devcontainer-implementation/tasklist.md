# DevContainer実装 - タスクリスト

## タスク概要
バックエンド開発向けのDev Container環境を段階的に実装します。
各タスクは独立して検証可能な単位で定義されています。

## フェーズ1: 最小構成（MVP）

### タスク1: ディレクトリ作成
- [ ] `backend/.devcontainer/`ディレクトリ作成
- [ ] `backend/.vscode/`ディレクトリ作成

**完了条件:**
- 必要なディレクトリが作成されている

**実行コマンド:**
```bash
mkdir -p backend/.devcontainer
mkdir -p backend/.vscode
```

---

### タスク2: devcontainer.json作成
- [ ] `backend/.devcontainer/devcontainer.json`作成
  - 基本設定（name, dockerComposeFile, service, workspaceFolder）
  - overrideCommand設定
  - runServices設定
  - VSCode拡張機能設定
  - VSCode settings設定
  - ポートフォワーディング設定
  - postCreateCommand設定
  - Git認証情報マウント設定

**完了条件:**
- devcontainer.jsonが設計書通りに作成されている
- JSONの構文エラーがない

**ファイル内容:**
設計書の「2. devcontainer.json設計」セクションを参照

---

### タスク3: Dev Container起動確認
- [ ] VSCodeでbackendフォルダを開く
- [ ] Dev Container拡張機能がインストールされているか確認
- [ ] 「Reopen in Container」で起動
- [ ] コンテナビルド・起動の確認
- [ ] 依存サービス起動確認（postgres、mailhog、minio）

**完了条件:**
- Dev Containerが正常に起動する
- VSCodeがコンテナに接続される
- ターミナルでコマンド実行可能

**確認コマンド（コンテナ内）:**
```bash
# Python環境確認
python --version
# → Python 3.11.x

# uv確認
uv --version

# .venv確認
ls -la /app/.venv

# 依存関係確認
uv run python -c "import fastapi; print(fastapi.__version__)"

# サービス接続確認
ping -c 1 postgres
ping -c 1 mailhog
ping -c 1 minio
```

---

### タスク4: VSCode拡張機能確認
- [ ] Python拡張機能がインストールされているか確認
- [ ] Pylance拡張機能がインストールされているか確認
- [ ] Ruff拡張機能がインストールされているか確認
- [ ] Pythonインタプリタが認識されているか確認（`/app/.venv/bin/python`）

**完了条件:**
- 必要な拡張機能がすべてインストールされている
- Pythonインタプリタが正しく設定されている

**確認方法:**
1. VSCodeの拡張機能パネルを開く
2. インストール済み拡張機能を確認
3. コマンドパレット → "Python: Select Interpreter" → `/app/.venv/bin/python`が選択されているか確認

---

### タスク5: 基本動作確認
- [ ] ターミナルでFastAPIアプリを起動
- [ ] http://localhost:8000 にアクセス
- [ ] http://localhost:8000/docs でSwagger UIにアクセス
- [ ] ホットリロード確認（コード編集→自動再起動）

**完了条件:**
- FastAPIアプリが正常起動する
- Swagger UIが表示される
- ホットリロードが機能する

**実行コマンド（コンテナ内）:**
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**確認方法:**
1. ブラウザで http://localhost:8000/docs を開く
2. `app/main.py`を編集して保存
3. ターミナルに再起動メッセージが表示されることを確認

---

## フェーズ2: 開発体験向上

### タスク6: デバッグ設定作成
- [ ] `backend/.vscode/launch.json`作成
  - FastAPIデバッグ設定
  - pytestデバッグ設定

**完了条件:**
- launch.jsonが設計書通りに作成されている
- JSONの構文エラーがない

**ファイル内容:**
設計書の「.vscode/launch.json（デバッグ設定）」セクションを参照

---

### タスク7: デバッグ機能確認
- [ ] FastAPIデバッグ設定で起動
- [ ] ブレークポイントを設定
- [ ] APIエンドポイントにアクセスしてブレークポイントで停止
- [ ] 変数の確認、ステップ実行の確認

**完了条件:**
- F5キーでFastAPIアプリがデバッグモードで起動する
- ブレークポイントで停止する
- 変数の値が確認できる

**確認方法:**
1. `app/api/v1/endpoints/health.py`にブレークポイントを設定
2. F5キーを押して「Python: FastAPI」設定を選択
3. ブラウザで http://localhost:8000/api/v1/health にアクセス
4. ブレークポイントで停止することを確認

---

### タスク8: VSCodeワークスペース設定作成
- [ ] `backend/.vscode/settings.json`作成
  - Pythonインタプリタパス設定
  - Ruff設定
  - フォーマット設定
  - テスト設定
  - ファイル除外設定

**完了条件:**
- settings.jsonが設計書通りに作成されている
- JSONの構文エラーがない

**ファイル内容:**
設計書の「.vscode/settings.json（ワークスペース設定）」セクションを参照

---

### タスク9: 自動フォーマット・Lint確認
- [ ] Pythonファイルを編集して保存
- [ ] 自動フォーマットが実行されることを確認
- [ ] Lint警告が表示されることを確認

**完了条件:**
- 保存時にRuffで自動フォーマットされる
- Lint警告がエディタに表示される

**確認方法:**
1. `app/main.py`を開く
2. 意図的にフォーマットを崩す（例: `import os;import sys`）
3. 保存（Cmd/Ctrl + S）
4. 自動的にフォーマットされることを確認

---

### タスク10: 推奨拡張機能リスト作成
- [ ] `backend/.vscode/extensions.json`作成

**完了条件:**
- extensions.jsonが設計書通りに作成されている
- JSONの構文エラーがない

**ファイル内容:**
設計書の「.vscode/extensions.json（推奨拡張機能）」セクションを参照

---

### タスク11: テスト実行確認
- [ ] VSCodeのTest Explorerを開く
- [ ] テストが認識されているか確認
- [ ] Test Explorerからテスト実行
- [ ] pytestデバッグ設定でテストをデバッグ実行

**完了条件:**
- Test Explorerでテストが表示される
- テストが実行できる
- テストのデバッグができる

**確認方法:**
1. VSCodeのTest Explorerアイコンをクリック
2. `tests/`以下のテストが表示されることを確認
3. テストを実行して成功することを確認
4. テストにブレークポイントを設定してデバッグ実行

---

## フェーズ3: ドキュメント整備

### タスク12: README.md更新
- [ ] `backend/README.md`にDev Container使用手順を追記
  - Dev Containerとは
  - 必要な前提条件
  - 起動方法
  - トラブルシューティング

**完了条件:**
- README.mdにDev Container関連の情報が追加されている
- 第三者がREADMEを読んで起動できる

**追記内容（例）:**
```markdown
## Dev Container（推奨）

### 必要な環境
- Docker Desktop
- VSCode
- Dev Containers拡張機能（ms-vscode-remote.remote-containers）

### 起動方法
1. VSCodeでbackendフォルダを開く
2. 右下の通知「Reopen in Container」をクリック
3. Dev Containerが自動的にビルド・起動

### 開発
- F5: FastAPIアプリをデバッグ起動
- Cmd/Ctrl + Shift + P → "Python: Run All Tests": テスト実行
- 保存時に自動フォーマット・Lint

### トラブルシューティング
- コンテナ再ビルド: Cmd/Ctrl + Shift + P → "Dev Containers: Rebuild Container"
- 依存関係の再インストール: `uv sync --reinstall`
```

---

### タスク13: 最終検証
- [ ] 受け入れ条件の確認
  - [ ] VSCodeでbackendフォルダを開くとDev Containerで起動を促すメッセージが表示される
  - [ ] Dev Container内でバックエンドの開発が可能
  - [ ] Dev Container内から依存サービスにアクセス可能
  - [ ] 必要なVSCode拡張機能が自動インストールされる
  - [ ] uvicornのホットリロードが正常に機能する
  - [ ] pytest、Ruffなどのツールがコンテナ内で実行可能
  - [ ] デバッガを使用してFastAPIアプリケーションをデバッグ可能

**完了条件:**
- すべての受け入れ条件を満たしている

**検証項目:**
1. Dev Container起動確認
2. 依存サービス接続確認（postgres、mailhog、minio）
3. VSCode拡張機能確認
4. ホットリロード確認
5. テスト実行確認
6. デバッグ確認
7. 自動フォーマット・Lint確認

---

### タスク14: 従来フローとの互換性確認
- [ ] Dev Containerを使わずに`docker-compose up`で起動
- [ ] 正常に動作することを確認
- [ ] Dev Container使用時との違いを確認

**完了条件:**
- 従来の開発フローも引き続き使用可能
- Dev Containerと従来フローが共存できる

**確認コマンド:**
```bash
# ホスト側で実行
docker-compose up -d
docker-compose logs -f backend

# 別ターミナルで確認
curl http://localhost:8000/docs
```

---

## タスク実行順序

```
Phase 1: 最小構成（MVP）
  Task 1 → Task 2 → Task 3 → Task 4 → Task 5

Phase 2: 開発体験向上
  Task 6 → Task 7 → Task 8 → Task 9 → Task 10 → Task 11

Phase 3: ドキュメント整備
  Task 12 → Task 13 → Task 14
```

## 進捗管理
- [ ] Phase 1: 最小構成（MVP）
- [ ] Phase 2: 開発体験向上
- [ ] Phase 3: ドキュメント整備

## 備考
- 各タスク完了後、動作確認を実施すること
- 問題が発生した場合は、前のタスクに戻って原因を特定すること
- コミットは各フェーズ完了時に実施すること
- `.vscode/`ディレクトリをGit管理するか検討（推奨: 管理する）

## 注意事項
- ホストの`backend/.venv`は削除済み（設計意図に反するため）
- docker-compose.dev.ymlは作成しない（既存のdocker-compose.ymlを活用）
- 既存のDockerfile.devは変更しない
