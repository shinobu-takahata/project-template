# リポジトリ構造定義書

## 概要

Amazon ECS を使用した Web アプリケーション開発テンプレートリポジトリの構造を定義します。

---

## トップレベル構成

```
project-template/
├── backend/                    # FastAPI バックエンドアプリケーション
├── frontend/                   # Next.js フロントエンドアプリケーション
├── cdk/                        # AWS CDK インフラコード
├── docs/                       # プロジェクト永続ドキュメント
├── .steering/                  # 作業単位ステアリングドキュメント（CDK配下に存在）
├── .devcontainer/              # DevContainer 設定
├── .github/                    # GitHub Actions ワークフロー
├── scripts/                    # ユーティリティスクリプト
├── requirements_definition_and_design/  # 要件定義・設計ドキュメント
├── docker-compose.yml          # ローカル開発環境定義
├── CLAUDE.md                   # Claude Code 開発ルール定義
└── README.md                   # プロジェクト概要
```

---

## ディレクトリ詳細

### `backend/` — FastAPI バックエンド

レイヤードアーキテクチャ（プレゼンテーション・アプリケーション・ドメイン・インフラ）で構成。

```
backend/
├── app/
│   ├── api/                    # プレゼンテーション層
│   │   └── v1/
│   │       ├── endpoints/      # エンドポイント定義（customers, orders, products, health）
│   │       └── router.py       # ルーター集約
│   ├── application/            # アプリケーション層
│   │   ├── customer/
│   │   │   ├── dtos/           # Data Transfer Objects
│   │   │   └── usecases/       # ユースケース実装
│   │   ├── order/
│   │   └── product/
│   ├── domain/                 # ドメイン層
│   │   ├── customer/
│   │   │   ├── entities/       # エンティティ
│   │   │   ├── value_objects/  # 値オブジェクト
│   │   │   └── repositories/   # リポジトリインターフェース
│   │   ├── order/
│   │   │   ├── services/       # ドメインサービス
│   │   │   └── ...
│   │   ├── product/
│   │   └── stock/
│   ├── infrastructure/         # インフラ層
│   │   ├── database/           # SQLAlchemy モデル
│   │   ├── repositories/       # リポジトリ実装
│   │   ├── email/              # SMTP クライアント
│   │   └── storage/            # S3 クライアント
│   ├── schemas/                # Pydantic スキーマ（API 入出力）
│   ├── core/                   # 設定・DB セッション
│   └── main.py                 # FastAPI アプリエントリポイント
├── alembic/                    # DB マイグレーション
│   └── versions/               # マイグレーションファイル
├── batch/                      # バッチ処理スクリプト
├── tests/
│   ├── unit/                   # ユニットテスト
│   │   ├── application/        # ユースケーステスト
│   │   ├── domain/             # ドメインテスト
│   │   └── mocks/              # モックリポジトリ
│   └── integration/            # 統合テスト（API エンドポイント）
├── Dockerfile.dev              # 開発用 Dockerfile
├── pyproject.toml              # 依存関係・ツール設定（uv）
└── alembic.ini                 # Alembic 設定
```

**技術スタック:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, uv

**コード品質ツール:** Ruff（lint/format）, mypy（型チェック）, pytest

---

### `frontend/` — Next.js フロントエンド

Next.js App Router（`app/` ディレクトリ）を採用。ルートセグメントごとにコロケーションパターンで整理。

```
frontend/
├── app/                        # Next.js App Router
│   ├── layout.tsx              # ルートレイアウト
│   ├── page.tsx                # トップページ
│   ├── error.tsx               # グローバルエラーハンドラ
│   └── customers/              # 顧客機能ルート
│       ├── layout.tsx
│       ├── page.tsx            # 顧客一覧
│       ├── new/                # 顧客新規作成
│       │   ├── _actions/       # Server Actions
│       │   ├── _components/    # ページ固有コンポーネント
│       │   └── page.tsx
│       └── [customerId]/       # 顧客詳細
│           ├── _actions/       # Server Actions
│           ├── _components/    # ページ固有コンポーネント
│           ├── _lib/           # fetcher 等ページ固有ユーティリティ
│           ├── loading.tsx
│           ├── error.tsx
│           ├── not-found.tsx
│           └── page.tsx
├── components/
│   └── ui/                     # shadcn/ui コンポーネント
├── lib/
│   ├── api-client.ts           # バックエンド API クライアント
│   └── utils.ts                # 汎用ユーティリティ
├── types/                      # 共通型定義
├── __mocks__/                  # Jest モック
├── docs/                       # フロントエンド固有ドキュメント
├── next.config.ts
├── biome.json                  # Biome（lint/format）設定
├── jest.config.js              # Jest 設定
└── tsconfig.json
```

**技術スタック:** Next.js 16, React 19, TypeScript, Tailwind CSS v4, shadcn/ui

**コード品質ツール:** Biome（lint/format）, Jest + Testing Library

**ディレクトリ規則:**
- `_actions/` — Server Actions（ページ固有）
- `_components/` — ページ固有コンポーネント（アンダースコアで非ルート化）
- `_lib/` — ページ固有のデータ取得・ユーティリティ
- `components/ui/` — 全体共有 UI コンポーネント（shadcn/ui）

---

### `cdk/` — AWS CDK インフラ

TypeScript で記述された AWS CDK コード。スタックごとに責務を分離。

```
cdk/
├── bin/
│   └── app.ts                  # CDK アプリエントリポイント・スタック初期化
├── lib/
│   ├── stacks/                 # CDK スタック定義
│   │   ├── network-stack.ts    # VPC・サブネット・NAT Gateway
│   │   ├── security-stack.ts   # セキュリティグループ・IAM
│   │   ├── database-stack.ts   # RDS（Aurora Serverless 等）
│   │   ├── ecr-stack.ts        # ECR リポジトリ
│   │   ├── compute-stack.ts    # ECS Fargate・ALB
│   │   ├── monitoring-stack.ts # CloudWatch・アラーム
│   │   └── orchestration-stack.ts  # スタック間依存の調整
│   └── config/                 # 環境別設定
│       ├── env-config.ts       # 設定型定義
│       ├── dev.ts              # 開発環境設定
│       └── prod.ts             # 本番環境設定
├── docker/
│   └── fluent-bit/             # ログルーティング用 Fluent Bit 設定
├── docs/
│   └── architecture/           # CDK 固有アーキテクチャドキュメント
├── .steering/                  # CDK 作業ステアリングドキュメント
├── cdk.json                    # CDK 設定
├── Dockerfile                  # CDK 実行用コンテナ
└── package.json
```

**スタック依存関係:** NetworkStack → SecurityStack → DatabaseStack → EcrStack → ComputeStack → MonitoringStack

---

### `docs/` — プロジェクト永続ドキュメント

プロジェクト全体の基本設計を記述。大きな設計変更時のみ更新。

```
docs/
├── architecture/               # 技術仕様書
│   ├── aws_infra.md            # AWS システム構成設計書
│   ├── local_dev.md            # ローカル開発環境設計書
│   ├── tools.md                # 開発ツールと手法
│   ├── performance.md          # パフォーマンス要件
│   ├── cost_estimate.md        # コスト見積もり
│   └── implements_aws_by_cdk_plan.md  # CDK 実装計画
├── assessment/                 # アセスメント・設計書テンプレート
│   ├── 01_business-flow.md
│   ├── 02_functional-requirements.md
│   ├── 03_screen-design.md
│   ├── 04_screen-transition.md
│   ├── 05_glossary.md
│   ├── 06_data-model.md
│   ├── 07_non-functional-requirements.md
│   ├── 08_role-permission.md
│   ├── 09_assessment-items.md
│   ├── 10_api-design.md
│   └── detailed_design/        # 詳細設計
├── repository-structure.md     # 本ドキュメント
├── ci-cd-pipeline.md           # CI/CD パイプライン説明
└── github-actions-deployment.md
```

---


### `.devcontainer/` — DevContainer 設定

VS Code DevContainer でのローカル開発環境設定。

```
.devcontainer/
├── backend-container/
│   └── devcontainer.json       # バックエンド開発用コンテナ設定
└── cdk-container/
    └── devcontainer.json       # CDK 開発用コンテナ設定
```

---

### `.github/` — GitHub Actions

```
.github/
└── workflows/
    ├── deploy-ecs.yml          # ECS への自動デプロイ
    └── deploy-with-approval.yml  # 承認ゲート付きデプロイ
```

---

### `scripts/` — ユーティリティスクリプト

```
scripts/
├── initial-push.sh             # 初回プッシュ用スクリプト
├── push-fluent-bit.sh          # Fluent Bit イメージプッシュ
└── setup-github-actions.sh     # GitHub Actions 環境変数・シークレット設定
```

---

### `requirements_definition_and_design/` — 要件定義・設計

プロジェクト計画・要件定義・設計のドキュメント群。テンプレートとして活用。

```
requirements_definition_and_design/
├── project_plan/               # プロジェクト計画書
├── non_functional/             # 非機能要件（セキュリティ・可用性・性能・保守性）
└── requirements_definition/
    ├── based_design/           # 基本設計テンプレート
    ├── detailed_design/        # 詳細設計テンプレート
    ├── quality/                # 品質要件
    └── test/                   # テスト計画
```

---

## ローカル開発環境構成（docker-compose）

| サービス   | ポート            | 用途                          |
|----------|-------------------|-------------------------------|
| backend  | 8000             | FastAPI アプリケーション         |
| postgres | 5432             | PostgreSQL 16 データベース       |
| mailhog  | 1025/8025        | SMTP サーバー / メール確認 Web UI |
| minio    | 9000/9001        | S3 互換ストレージ / 管理コンソール |
| cdk      | —                | CDK 実行環境（profile: cdk）     |

---

## ファイル配置ルール

| ファイル種別                     | 配置場所                                      |
|-------------------------------|---------------------------------------------|
| API エンドポイント               | `backend/app/api/v1/endpoints/`             |
| ユースケース                    | `backend/app/application/{domain}/usecases/` |
| ドメインエンティティ             | `backend/app/domain/{domain}/entities/`      |
| 値オブジェクト                  | `backend/app/domain/{domain}/value_objects/` |
| リポジトリインターフェース         | `backend/app/domain/{domain}/repositories/`  |
| リポジトリ実装                  | `backend/app/infrastructure/repositories/`   |
| DB モデル                      | `backend/app/infrastructure/database/`       |
| API スキーマ（Pydantic）        | `backend/app/schemas/`                       |
| DB マイグレーション              | `backend/alembic/versions/`                  |
| Next.js ページ固有コンポーネント  | `frontend/app/{route}/_components/`          |
| Next.js Server Actions         | `frontend/app/{route}/_actions/`             |
| 共有 UI コンポーネント           | `frontend/components/ui/`                    |
| 型定義（フロントエンド全体共有）  | `frontend/types/`                            |
| CDK スタック                    | `cdk/lib/stacks/`                            |
| 環境別 CDK 設定                 | `cdk/lib/config/`                            |
| 永続的プロジェクトドキュメント    | `docs/`                                      |
| 作業単位ドキュメント             | `.steering/[YYYYMMDD]-[タイトル]/`            |
| GitHub Actions ワークフロー     | `.github/workflows/`                         |
| ユーティリティスクリプト         | `scripts/`                                   |
