# リポジトリ構造定義書

## 概要
本ドキュメントは、プロジェクトのディレクトリ構造、ファイル配置ルール、および各ディレクトリの役割を定義します。

## ディレクトリ構造

```
project-template/
├── .github/                    # GitHub関連設定
│   ├── workflows/              # GitHub Actionsワークフロー
│   │   ├── backend-ci.yml
│   │   ├── frontend-ci.yml
│   │   ├── deploy.yml
│   │   └── cdk-deploy.yml
│   ├── ISSUE_TEMPLATE/         # Issueテンプレート
│   └── PULL_REQUEST_TEMPLATE.md
│
├── .steering/                  # 作業単位のステアリングファイル
│   └── [YYYYMMDD]-[開発タイトル]/
│       ├── requirements.md     # 要求内容
│       ├── design.md           # 設計
│       └── tasklist.md         # タスクリスト
│
├── docs/                       # 永続的ドキュメント
│   ├── architecture/           # 技術仕様書
│   │   ├── aws_infra.md
│   │   ├── local_dev.md
│   │   ├── tools.md
│   │   └── performance.md
│   └── repository-structure.md # 本ドキュメント
│
├── backend/                    # バックエンドアプリケーション（レイヤードアーキテクチャ）
│   ├── app/                    # アプリケーションコード
│   │   ├── presentation/       # プレゼンテーション層（API）
│   │   │   ├── api/
│   │   │   │   ├── v1/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── endpoints/
│   │   │   │   │       ├── users.py
│   │   │   │   │       └── auth.py
│   │   │   │   └── deps.py     # 依存関係
│   │   │   └── schemas/        # Pydanticスキーマ（リクエスト/レスポンス）
│   │   │       ├── __init__.py
│   │   │       ├── user.py
│   │   │       └── auth.py
│   │   ├── application/        # アプリケーション層（ユースケース実装）
│   │   │   └── services/       # アプリケーションサービス
│   │   │       ├── __init__.py
│   │   │       ├── user_service.py
│   │   │       └── auth_service.py
│   │   ├── domain/             # ドメイン層（ビジネスルール）
│   │   │   ├── entities/       # エンティティ（IDを持つドメインオブジェクト）
│   │   │   │   ├── __init__.py
│   │   │   │   └── user.py
│   │   │   ├── value_objects/  # 値オブジェクト（不変、等価性で比較）
│   │   │   │   ├── __init__.py
│   │   │   │   ├── email.py
│   │   │   │   └── user_id.py
│   │   │   ├── services/       # ドメインサービス（複数エンティティにまたがるロジック）
│   │   │   │   ├── __init__.py
│   │   │   │   └── user_domain_service.py
│   │   │   └── repositories/   # リポジトリインターフェース
│   │   │       ├── __init__.py
│   │   │       └── user_repository.py
│   │   ├── infrastructure/     # インフラストラクチャ層（外部連携）
│   │   │   ├── database/
│   │   │   │   ├── models/     # SQLAlchemyモデル
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── user.py
│   │   │   │   └── repositories/ # リポジトリ実装
│   │   │   │       ├── __init__.py
│   │   │   │       └── user_repository.py
│   │   │   ├── external/       # 外部サービス連携
│   │   │   │   ├── email.py
│   │   │   │   └── s3.py
│   │   │   └── config.py       # 環境設定
│   │   ├── core/               # 共通機能
│   │   │   ├── database.py     # DB接続
│   │   │   ├── security.py     # セキュリティ
│   │   │   └── config.py       # 設定管理
│   │   └── main.py             # アプリケーションエントリーポイント
│   ├── tests/                  # テストコード
│   │   ├── unit/               # ユニットテスト
│   │   │   └── test_user_service.py
│   │   ├── integration/        # 統合テスト
│   │   │   └── test_user_api.py
│   │   └── conftest.py         # pytestフィクスチャ
│   ├── alembic/                # マイグレーション
│   │   ├── versions/
│   │   └── env.py
│   ├── scripts/                # スクリプト
│   │   └── seed_data.py
│   ├── Dockerfile              # 本番用Dockerfile
│   ├── Dockerfile.dev          # 開発用Dockerfile
│   ├── pyproject.toml          # uvプロジェクト設定
│   ├── uv.lock                 # 依存関係ロック
│   └── alembic.ini             # Alembic設定
│
├── frontend/                   # フロントエンドアプリケーション
│   ├── src/
│   │   ├── app/                # App Router
│   │   │   ├── layout.tsx      # ルートレイアウト
│   │   │   ├── page.tsx        # トップページ
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── dashboard/
│   │   │       └── page.tsx
│   │   ├── components/         # 再利用可能なコンポーネント
│   │   │   ├── ui/             # UIコンポーネント
│   │   │   │   ├── Button.tsx
│   │   │   │   └── Input.tsx
│   │   │   └── features/       # 機能別コンポーネント
│   │   │       └── UserProfile.tsx
│   │   ├── lib/                # ユーティリティ・ヘルパー
│   │   │   ├── api.ts          # API クライアント
│   │   │   └── utils.ts
│   │   ├── hooks/              # カスタムフック
│   │   │   └── useUser.ts
│   │   ├── types/              # TypeScript型定義
│   │   │   └── user.ts
│   │   └── styles/             # グローバルスタイル
│   │       └── globals.css
│   ├── public/                 # 静的ファイル
│   │   ├── images/
│   │   └── favicon.ico
│   ├── __tests__/              # テストコード
│   │   └── components/
│   │       └── Button.test.tsx
│   ├── .env.local              # ローカル環境変数（.gitignore）
│   ├── .env.local.example      # 環境変数テンプレート
│   ├── biome.json              # Biome設定
│   ├── next.config.js          # Next.js設定
│   ├── tailwind.config.ts      # Tailwind CSS設定
│   ├── tsconfig.json           # TypeScript設定
│   ├── package.json
│   └── package-lock.json
│
├── cdk/                        # AWS CDK（インフラコード）
│   ├── bin/
│   │   └── app.ts              # CDKアプリエントリーポイント
│   ├── lib/                    # CDKスタック定義
│   │   ├── network-stack.ts    # VPC、サブネット
│   │   ├── database-stack.ts   # Aurora
│   │   ├── compute-stack.ts    # ECS、Fargate
│   │   └── frontend-stack.ts   # Amplify
│   ├── test/                   # CDKテスト
│   │   └── app.test.ts
│   ├── cdk.json                # CDK設定
│   ├── biome.json              # Biome設定
│   ├── tsconfig.json
│   ├── package.json
│   ├── package-lock.json
│   └── Dockerfile              # CDKコンテナ用
│
├── docker-compose.yml          # ローカル開発環境
├── .gitignore
├── .pre-commit-config.yaml     # Pre-commit設定
├── README.md                   # プロジェクト概要
└── CLAUDE.md                   # 開発プロセス定義
```

## ディレクトリの役割

### ルートディレクトリ

#### `.github/`
GitHub関連の設定ファイルを格納

- **workflows/**: GitHub Actions CI/CDワークフロー定義
- **ISSUE_TEMPLATE/**: Issueテンプレート
- **PULL_REQUEST_TEMPLATE.md**: PRテンプレート

#### `.steering/`
作業単位のステアリングファイル（要件、設計、タスクリスト）

- **命名規則**: `[YYYYMMDD]-[開発タイトル]/`
- **内容**: 特定の開発作業における「今回何をするか」を定義
- **管理**: 作業完了後も履歴として保持

#### `docs/`
永続的なプロジェクトドキュメント

- **architecture/**: 技術仕様書、アーキテクチャ設計書
- **repository-structure.md**: 本ドキュメント

### バックエンド（`backend/`）

#### レイヤードアーキテクチャ
```
Presentation層（API）
    ↓
Application層（ビジネスロジック）
    ↓
Domain層（ビジネスルール）
    ↓
Infrastructure層（外部連携・永続化）
```

#### プレゼンテーション層（`app/presentation/`）
ユーザーインターフェース（API）を提供

- **api/v1/endpoints/**: APIエンドポイント定義
- **api/deps.py**: 依存関係注入（認証、DB接続等）
- **schemas/**: Pydanticスキーマ（リクエスト/レスポンス）
  - APIの入出力データ構造を定義
  - バリデーション、シリアライゼーション

#### アプリケーション層（`app/application/`）
ユースケースを実装し、ドメイン層を調整

- **services/**: アプリケーションサービス
  - ユースケースの実装（1サービス = 1ユースケース）
  - ドメイン層とインフラ層を連携
  - トランザクション境界の管理
  - 例: `UserService.register_user()`, `AuthService.login()`

#### ドメイン層（`app/domain/`）
ビジネスルールとビジネスロジックの中核（DDD）

- **entities/**: エンティティ
  - 一意のIDを持つドメインオブジェクト
  - ライフサイクルを持つ
  - ビジネスルールをカプセル化
  - 例: `User`, `Order`, `Product`

- **value_objects/**: 値オブジェクト
  - 不変（immutable）
  - 等価性で比較（IDではなく値で比較）
  - ドメイン概念を表現
  - 例: `Email`, `UserId`, `Money`, `Address`

- **services/**: ドメインサービス
  - 複数のエンティティにまたがるビジネスロジック
  - 単一エンティティに属さない操作
  - 例: `UserDomainService.check_duplicate_email()`

- **repositories/**: リポジトリインターフェース
  - データアクセスの抽象化（抽象基底クラス）
  - インフラ層への依存を排除
  - ドメインオブジェクトの永続化・取得

#### インフラストラクチャ層（`app/infrastructure/`）
外部システムとの連携、永続化を担当

- **database/models/**: SQLAlchemyモデル
  - データベーステーブル定義
  - ORMマッピング
- **database/repositories/**: リポジトリ実装
  - ドメイン層のリポジトリインターフェースを実装
  - 実際のDB操作を実行
- **external/**: 外部サービス連携
  - email.py: メール送信（MailHog/SES）
  - s3.py: ファイルストレージ（MinIO/S3）
- **config.py**: インフラ設定

#### 共通機能（`app/core/`）
全層で使用される共通機能

- **database.py**: データベース接続、セッション管理
- **security.py**: 認証、認可ロジック
- **config.py**: 環境変数、設定管理

#### `tests/`
テストコード

- **unit/**: ユニットテスト（サービス層、ユーティリティ）
- **integration/**: 統合テスト（APIエンドポイント）
- **conftest.py**: pytestフィクスチャ、テスト設定

#### `alembic/`
データベースマイグレーション

- **versions/**: マイグレーションファイル
- **env.py**: Alembic環境設定

#### `scripts/`
管理スクリプト

- **seed_data.py**: シードデータ投入
- その他バッチ処理

### フロントエンド（`frontend/`）

#### `src/app/`
Next.js App Router

- **layout.tsx**: レイアウト定義
- **page.tsx**: ページコンポーネント
- **ディレクトリベースルーティング**: `login/page.tsx` → `/login`

#### `src/components/`
再利用可能なReactコンポーネント

- **ui/**: 汎用UIコンポーネント（Button、Input等）
- **features/**: 機能別コンポーネント（UserProfile等）

#### `src/lib/`
ユーティリティ、ヘルパー関数

- **api.ts**: バックエンドAPIクライアント
- **utils.ts**: 共通ユーティリティ

#### `src/hooks/`
カスタムReactフック

- **命名規則**: `use[フック名].ts`

#### `src/types/`
TypeScript型定義

- **内容**: APIレスポンス型、共通型定義

#### `src/styles/`
グローバルスタイル

- **globals.css**: Tailwind CSSベーススタイル

#### `public/`
静的ファイル

- **images/**: 画像ファイル
- **favicon.ico**: ファビコン

#### `__tests__/`
テストコード

- **構造**: src/と同じ構造でテストファイルを配置

### インフラ（`cdk/`）

#### `bin/`
CDKアプリケーションエントリーポイント

- **app.ts**: スタックの初期化、デプロイ設定

#### `lib/`
CDKスタック定義

- **network-stack.ts**: VPC、サブネット、セキュリティグループ
- **database-stack.ts**: Aurora PostgreSQL
- **compute-stack.ts**: ECS、Fargate、ALB
- **frontend-stack.ts**: Amplify

#### `test/`
CDKスタックのテスト

## ファイル配置ルール

### 命名規則

#### Python（バックエンド）
- **ファイル名**: スネークケース（`user_service.py`）
- **クラス名**: パスカルケース（`UserService`）
- **関数名**: スネークケース（`get_user`）
- **定数**: アッパースネークケース（`MAX_RETRY_COUNT`）

#### TypeScript（フロントエンド・CDK）
- **ファイル名**:
  - コンポーネント: パスカルケース（`Button.tsx`）
  - ユーティリティ: キャメルケース（`api.ts`）
- **コンポーネント名**: パスカルケース（`Button`）
- **関数名**: キャメルケース（`getUser`）
- **定数**: アッパースネークケース（`API_BASE_URL`）

### インポート順序

#### Python
```python
# 1. 標準ライブラリ
import os
from typing import List

# 2. サードパーティライブラリ
from fastapi import APIRouter
from sqlalchemy.orm import Session

# 3. ローカルモジュール
from app.core.config import settings
from app.models.user import User
```

#### TypeScript
```typescript
// 1. React関連
import { useState } from 'react'

// 2. サードパーティライブラリ
import axios from 'axios'

// 3. ローカルモジュール
import { Button } from '@/components/ui/Button'
import { getUser } from '@/lib/api'

// 4. スタイル
import styles from './styles.module.css'
```

### 環境変数管理

#### 配置場所
- **バックエンド**: `backend/.env.local`
- **フロントエンド**: `frontend/.env.local`
- **テンプレート**: `.env.local.example`（Git管理対象）

#### 命名規則
- **すべて大文字**: `DATABASE_URL`
- **アンダースコア区切り**: `SMTP_HOST`
- **フロントエンド公開変数**: `NEXT_PUBLIC_API_URL`

### テストファイル配置

#### バックエンド
```
backend/
├── app/
│   └── services/
│       └── user_service.py
└── tests/
    └── unit/
        └── test_user_service.py
```

#### フロントエンド
```
frontend/
├── src/
│   └── components/
│       └── Button.tsx
└── __tests__/
    └── components/
        └── Button.test.tsx
```

## 新規ファイル追加ガイドライン

### APIエンドポイント追加（DDDフロー）

#### ドメイン層から作成
1. **エンティティ作成**: `backend/app/domain/entities/[エンティティ名].py`
   - ビジネスルールを持つドメインオブジェクト
2. **値オブジェクト作成**（必要に応じて）: `backend/app/domain/value_objects/[値オブジェクト名].py`
   - ドメイン概念を表現する不変オブジェクト
3. **ドメインサービス作成**（必要に応じて）: `backend/app/domain/services/[ドメインサービス名].py`
   - 複数エンティティにまたがるロジック
4. **リポジトリインターフェース作成**: `backend/app/domain/repositories/[エンティティ名]_repository.py`
   - データアクセスの抽象化

#### インフラ層の実装
5. **SQLAlchemyモデル作成**: `backend/app/infrastructure/database/models/[エンティティ名].py`
   - データベーステーブル定義
6. **リポジトリ実装作成**: `backend/app/infrastructure/database/repositories/[エンティティ名]_repository.py`
   - リポジトリインターフェースの具象実装
7. **マイグレーション生成**: `alembic revision --autogenerate -m "Add [エンティティ名] table"`

#### アプリケーション層の実装
8. **アプリケーションサービス作成**: `backend/app/application/services/[エンティティ名]_service.py`
   - ユースケースの実装

#### プレゼンテーション層の実装
9. **Pydanticスキーマ作成**: `backend/app/presentation/schemas/[エンティティ名].py`
   - リクエスト/レスポンスの型定義
10. **APIエンドポイント作成**: `backend/app/presentation/api/v1/endpoints/[リソース名].py`
    - HTTPエンドポイントの定義
11. **ルーター追加**: `backend/app/presentation/api/v1/__init__.py`

#### テスト作成
12. **ユニットテスト作成**: `tests/unit/domain/`, `tests/unit/application/`
13. **統合テスト作成**: `tests/integration/`

### フロントエンドページ追加
1. `frontend/src/app/[ページ名]/page.tsx`作成
2. 必要に応じて`layout.tsx`作成
3. 対応するコンポーネントを`src/components/`に作成

### CDKスタック追加
1. `cdk/lib/[スタック名]-stack.ts`作成
2. `cdk/bin/app.ts`にスタックインスタンス追加
3. 対応するテスト作成（`test/`）

## レイヤー間の依存関係ルール

### 依存の方向
```
Presentation → Application → Domain ← Infrastructure
                                ↑
                              Core
```

### ルール
1. **上位層は下位層に依存できる**
   - Presentation → Application → Domain
   - Application → Domain
   - Infrastructure → Domain

2. **下位層は上位層に依存できない**
   - Domain層はどの層にも依存しない（純粋なビジネスロジック）
   - Application層はPresentation層に依存しない

3. **依存性逆転の原則**
   - Infrastructure層はDomain層のインターフェース（リポジトリ）を実装
   - Application層はDomain層のインターフェースを使用
   - 具体的な実装（Infrastructure）への依存を避ける

## 禁止事項

### やってはいけないこと
- ❌ Domain層でInfrastructure層の具象クラスを直接使用
- ❌ Domain層でPresentationのスキーマを使用
- ❌ Presentation層でInfrastructureのモデルを直接返却
- ❌ 層をスキップした依存（Presentation → Infrastructure直接）
- ❌ `.env.local`をGit管理対象にする
- ❌ テストファイルをソースコードと同じディレクトリに配置
- ❌ 本番用の秘密情報をコードに直接記述

### 推奨される代替案
- ✅ Domain層ではリポジトリインターフェースを定義
- ✅ Domain層では純粋なビジネスオブジェクトを使用
- ✅ Presentation層ではスキーマに変換して返却
- ✅ レイヤードアーキテクチャの依存ルールに従う
- ✅ `.env.local.example`をテンプレートとして管理
- ✅ 専用のテストディレクトリに配置
- ✅ 環境変数、AWS Secrets Managerで管理

## メンテナンスルール

### 定期的な見直し
- 大規模な機能追加時にディレクトリ構造を見直し
- 不要になったファイルは削除（コミット履歴に残る）
- READMEとドキュメントを最新状態に保つ

### リファクタリング
- ファイル移動時は必ずインポートパスを更新
- 大規模な構造変更はPRで明示的にレビュー
- 影響範囲を確認してからコミット

## 更新履歴
- 2026-01-19: 初版作成
