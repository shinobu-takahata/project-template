# Project Template

ハードスキルをアップするためのプラクティス用リポジトリです。
現在、主に以下を管理しています。
- Amazon ECSを使用したWebアプリケーション開発のためのIaC（AWS CDK）
- FastAPIを用いたバックエンドアプリケーションのサンプルコード
  - レイヤードアーキテクチャやDDDの基本概念の表現
- GitHub Actionsを用いたCI/CDパイプライン
- Claude Codeを用いたいくつかの機能（スキル、サブエージェント）

※CI/CDパイプラインについては、現在AWS環境を closeしているため動作しない

今後、以下を追加していきます。
- Next.jsを用いたフロントエンドのサンプルコード
- エンタープライズアーキテクチャのためによく使用するようなパターンのAWS構成用のCDKのコード


今後学習していこうと考えている内容
- 単体テストの体系理解
- ログおよびオブザーバビリティ設計
- ソフトウェアアーキテクチャ全般
- 生成AI活用の追従
- 大規模システムになっても耐えうるようにするためのパフォーマンスに関する設計知識
- ソフトスキルの体系化

## 技術スタック

| レイヤー | 技術 |
|---|---|
| インフラ (IaC) | AWS CDK (TypeScript) |
| バックエンド | FastAPI (Python 3.11) + SQLAlchemy + Alembic |
| フロントエンド | Next.js |
| ローカル環境 | Docker / docker-compose / DevContainer |
| パッケージ管理 | uv (Python), npm (Node.js) |
| コード品質 | Ruff (lint/format), pytest |

## アーキテクチャ概要

```
Client → Route53 → Amplify (Frontend: Next.js)
                 → ALB → ECS Fargate (Backend: FastAPI) → Aurora PostgreSQL
```

- **フロントエンド**: AWS Amplifyでホスティング
- **バックエンド**: ECS Fargate + ALB構成、マルチAZ対応
- **データベース**: Aurora PostgreSQL
- **ログ**: Fluent Bit経由でCloudWatch Logs

## ディレクトリ構成

```
.
├── backend/          # FastAPI バックエンドアプリケーション（レイヤードアーキテクチャ）
├── frontend/         # Next.js フロントエンドアプリケーション
├── cdk/              # AWS CDK インフラコード
├── docs/             # 永続的な設計ドキュメント
│   └── architecture/ # AWS構成・ローカル環境・パフォーマンス等
├── .steering/        # 作業単位のステアリングドキュメント（開発履歴）
├── scripts/          # デプロイ・セットアップスクリプト
├── docker-compose.yml
└── CLAUDE.md         # Claude Code向け開発ルール定義
```
