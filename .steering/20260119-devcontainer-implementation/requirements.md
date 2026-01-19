# DevContainer実装 - 要求内容

## 概要
VSCodeのDev Container機能を実装し、バックエンド開発において環境構築なしにコンテナ内で開発できる環境を整備します。

## 目的
- Docker環境があれば即座にバックエンド開発を開始できる
- ホストマシンへの依存を最小化
- チーム全体で統一された開発環境を提供
- VSCodeの拡張機能やツールを自動セットアップ

## 背景
現在のプロジェクトでは、docker-composeによるローカル開発環境が構築されています。

### 現在の設計方針（[local_dev.md](../../docs/architecture/local_dev.md)より）
- **フロントエンド**: ホストマシンで直接実行（高速なホットリロード優先）
- **バックエンド**: Dockerコンテナで実行
- **開発支援ツール**: Dockerコンテナで実行（PostgreSQL、MailHog、MinIO）
- **CDK**: Dockerコンテナで実行（profileで制御）

### 課題
現状、バックエンド開発において以下の課題があります：

1. **IDE統合の欠如**
   - エディタとコンテナ環境が分離している
   - デバッグやLint結果がリアルタイムに反映されにくい
   - コンテナ内でのテスト実行やコマンド実行が煩雑

2. **開発体験の低下**
   - VSCodeでコードを編集しているが、実行環境はコンテナ内
   - Python拡張機能がコンテナ内のインタプリタを認識しにくい
   - デバッグ設定が複雑

## 要求内容

### 機能要件

#### 1. Dev Container構成
- **ターゲット**: バックエンド開発のみ
- **スコープ外**: フロントエンド（ホスト実行を継続）、CDK（必要に応じて別途検討）

#### 2. バックエンドDev Container
- Python 3.11環境
- uv、Ruff、mypyなどのツールを自動インストール
- PostgreSQL、MailHog、MinIOなどの依存サービスへの接続
- VSCode拡張機能の自動インストール:
  - Python (ms-python.python)
  - Pylance (ms-python.vscode-pylance)
  - Ruff (charliermarsh.ruff)
  - テスト関連拡張機能

#### 3. docker-composeとの統合
- 既存のdocker-compose.ymlサービス（postgres、mailhog、minio）を活用
- Dev Containerから依存サービスへアクセス可能
- `devcontainer.json`で`dockerComposeFile`を指定し、既存サービスと統合

#### 4. 開発ツールの統合
- デバッガ設定（launch.json）
- uvicornのデバッグ実行
- pytest実行設定
- Ruffによる自動フォーマット・リント

### 非機能要件

#### 1. 開発体験
- VSCodeでbackendフォルダを開くだけで自動的にコンテナが起動
- ホットリロードが正常に動作（uvicorn --reload）
- ターミナルからのコマンド実行が可能
- Gitコミット、プッシュがコンテナ内から可能

#### 2. パフォーマンス
- ボリュームマウントによるファイル同期のパフォーマンス最適化
- 依存関係のキャッシュ活用

#### 3. 互換性
- 既存のdocker-compose環境と共存可能
- 従来のローカル開発環境（docker-compose up）も引き続き使用可能
- フロントエンドはホスト実行を継続（変更なし）

## 受け入れ条件

### 必須条件
1. `backend/.devcontainer/`ディレクトリが作成され、適切な設定ファイルが配置されている
2. VSCodeでbackendフォルダを開くと、Dev Containerでの起動を促すメッセージが表示される
3. Dev Container内でバックエンドの開発が可能
4. Dev Container内から依存サービス（postgres、mailhog、minio）にアクセス可能
5. 必要なVSCode拡張機能が自動インストールされる
6. uvicornのホットリロード（--reload）が正常に機能する
7. pytest、Ruffなどのツールがコンテナ内で実行可能
8. デバッガを使用してFastAPIアプリケーションをデバッグ可能

### 任意条件
1. Dev Container使用手順のドキュメント化（README.mdまたはlocal_dev.mdへの追記）
2. トラブルシューティングガイドの作成
3. launch.jsonでのデバッグ設定

## 制約事項

### 技術的制約
- Docker Desktop（またはDocker互換環境）が必須
- VSCodeのDev Container拡張機能（ms-vscode-remote.remote-containers）が必要
- M1/M2 Macでのarm64アーキテクチャ対応も考慮

### 既存環境への影響
- 既存のdocker-compose.ymlは極力変更しない（または後方互換性を保つ）
- フロントエンドの開発ワークフロー（ホスト実行）は変更しない
- 従来のdocker-composeベースの開発フローを壊さない

### 開発スコープ
- 本番環境のデプロイ設定は対象外
- CI/CD環境への影響は最小限に留める
- フロントエンドのDev Containerは今回の対象外

## 参考情報

### 現在のプロジェクト構成
- [docker-compose.yml](../../docker-compose.yml): バックエンド、PostgreSQL、MailHog、MinIO、CDKを定義
- [backend/Dockerfile.dev](../../backend/Dockerfile.dev): 開発用Dockerfileが存在
- frontend/: ホストで実行する前提の構成（変更なし）
- cdk/Dockerfile: CDK実行用Dockerfileが存在

### Dev Container参考資料
- [Dev Containers公式ドキュメント](https://code.visualstudio.com/docs/devcontainers/containers)
- [Dev Container仕様](https://containers.dev/)
- [docker-composeとの統合](https://code.visualstudio.com/docs/devcontainers/docker-compose)

## 期待される効果

### 開発者体験の向上
- バックエンド開発における新規メンバーのオンボーディング時間を大幅短縮
- IDE統合による生産性向上（コード補完、リアルタイムLint、デバッグ）
- 「私の環境では動く」問題の解消

### 保守性の向上
- 環境構築手順のコード化
- チーム全体で統一されたバックエンド開発環境
- ドキュメント更新の負担軽減

### フロントエンド開発との分離
- フロントエンドは引き続きホストで高速に実行
- バックエンドのみコンテナで実行し、責務を明確化
