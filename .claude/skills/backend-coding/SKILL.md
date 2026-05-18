---
name: backend-coding
description: "FastAPI + レイヤードアーキテクチャでバックエンドを実装するときに必ず参照するスキル。アーキテクチャ構成・ディレクトリ配置・エラーハンドリング・トランザクション境界・ロギング・共通レスポンス形式のベストプラクティスをガイドする。バックエンドのコードを書く・実装する・APIエンドポイントやユースケースを追加するときは必ずこのスキルを参照する。"
---

# FastAPI バックエンドコーディングガイド

---

## アーキテクチャ原則

バックエンドは **4層のレイヤードアーキテクチャ** を採用する。依存は必ず上位層 → 下位層の一方向のみ。

```
Presentation層（FastAPI）
 ・HTTPリクエスト/レスポンスの処理
 ・Pydantic によるリクエストバリデーション
 ・Application層を呼び出すだけ — ビジネスロジックを書かない

Application層（ユースケース）
 ・ユースケースの実行順序を制御
 ・トランザクション境界の管理
 ・Domain層と Infrastructure層を組み合わせる

Domain層（ビジネスルール）
 ・集約・エンティティ・値オブジェクト
 ・ドメインサービス・ドメインイベント
 ・リポジトリインターフェース定義
 ・外部依存ゼロ — import できるのは標準ライブラリと他 domain モジュールのみ

Infrastructure層（外部連携）
 ・リポジトリ実装（SQLAlchemy + PostgreSQL）
 ・外部サービス連携
 ・環境設定・DB 接続
```

### 技術スタック

| コンポーネント | 採用技術 |
|---|---|
| Web フレームワーク | FastAPI |
| ORM | SQLAlchemy |
| データベース | PostgreSQL 15 |
| マイグレーション | Alembic |
| バリデーション | Pydantic |
| テスト | pytest |

---

## ディレクトリ構造と配置ルール

```
backend/
└── app/
    ├── presentation/
    │   ├── api/v1/endpoints/  # FastAPI ルーター
    │   └── schemas/           # Pydantic スキーマ（Request / Response）
    ├── application/
    │   └── services/          # ユースケース（アプリケーションサービス）
    ├── domain/
    │   ├── entities/          # エンティティ・集約ルート
    │   ├── value_objects/     # 値オブジェクト
    │   ├── services/          # ドメインサービス
    │   └── repositories/      # リポジトリインターフェース（ABC）
    ├── infrastructure/
    │   └── database/
    │       ├── models/        # SQLAlchemy モデル
    │       └── repositories/  # リポジトリ実装
    └── core/                  # DB 接続・設定・セキュリティ共通機能
```

| 実装対象 | 配置先 |
|---|---|
| FastAPI エンドポイント | `presentation/api/v1/endpoints/` |
| リクエスト/レスポンス型 | `presentation/schemas/` |
| ユースケースクラス | `application/services/` |
| 集約・エンティティ | `domain/entities/` |
| 値オブジェクト | `domain/value_objects/` |
| ドメインサービス | `domain/services/` |
| リポジトリ IF（抽象） | `domain/repositories/` |
| リポジトリ実装 | `infrastructure/database/repositories/` |
| SQLAlchemy モデル | `infrastructure/database/models/` |

### SQLAlchemy モデルが存在しない場合

実装対象テーブルに対応するモデルが `infrastructure/database/models/` になければ、実装の一部として新規作成する。
モデルの書き方は **`backend/README_SQLAlchemy.md`** を参照すること（Mapped 型アノテーション・リレーションシップ・Enum・クエリパターンなどのガイドが記載されている）。

---

## 共通レスポンス形式

**すべての API レスポンスはこの形式に統一する。**

```json
// 成功（単一リソース）
{ "data": { ... } }

// 一覧（ページネーション付き）
{ "data": [ ... ], "pagination": { "total": 100, "page": 1, "per_page": 20 } }

// エラー
{ "error": { "code": "ORDER_NOT_FOUND", "message": "..." } }
```

- `data` キーを必ずラップする。裸の JSON オブジェクト/配列を返さない
- エラーレスポンスの `code` は SCREAMING_SNAKE_CASE、`message` は人間が読める文字列

---

## エラーハンドリング

例外は発生した層で定義し、**上位層でキャッチして HTTP レスポンスに変換する**。Domain層に HTTP や外部ライブラリの例外クラスを持ち込まない。

| 例外の種類 | 発生層 | HTTP | 説明 |
|---|---|---|---|
| バリデーションエラー | Presentation（Pydantic） | 400 | 型・フォーマット不正 |
| ドメイン例外 | Domain | 409 | ビジネスルール違反 |
| リソース未検出 | Application | 404 | ID に対応するエンティティが存在しない |
| インフラエラー | Infrastructure | 500 | DB エラー・外部サービス障害 |

---

## トランザクション境界

トランザクションは **Application層（ユースケース）単位** で管理する。

- 1 ユースケース = 1 トランザクション
- Domain層はトランザクションを意識しない（`db` を受け取らない）
- `commit()` / `rollback()` は Application層または Infrastructure層のリポジトリ実装内で呼び出す

```python
# Application層の例
async def execute(self, command: CreateOrderCommand) -> OrderId:
    async with self.unit_of_work:          # トランザクション開始
        order = self.order_domain_service.create_order(...)
        await self.order_repository.save(order)
        await self.unit_of_work.commit()   # コミット
    return order.id
```

---

## ロギング方針

| ログレベル | 用途 |
|---|---|
| INFO | リクエスト受信・ユースケース完了・ドメインイベント発行 |
| WARNING | ビジネスルール違反（ドメイン例外） |
| ERROR | 予期しない例外・インフラエラー |

- リクエスト ID（`X-Request-ID`）をすべてのログに付与し、トレーサビリティを確保する
- Domain層にロガーを持ち込まない — イベント記録はドメインイベント経由で行う

---

## 認証・認可

| 項目 | 方針 |
|---|---|
| 認証方式 | JWT（Bearer トークン）を推奨 |
| 認可 | FastAPI の `Depends()` を使ったミドルウェアで実装 |
| トークン検証 | `presentation/api/deps.py` に集約する |
