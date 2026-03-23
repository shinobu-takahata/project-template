# バックエンド詳細設計書 - 注文管理システム（OrderHub）

## 1. ドキュメント概要

### 目的

本ドキュメントは、注文管理システム（OrderHub）のバックエンドに関する詳細設計をまとめた文書である。各設計領域の概要を示し、詳細については関連ドキュメントへ参照する形で構成する。

開発担当者はこのドキュメントを起点として、各詳細ドキュメントを参照しながら実装を進めること。

### 対象読者

- バックエンドエンジニア
- レビュアー・設計承認者

### 関連ドキュメント

| 分類 | ドキュメント名 | パス |
|---|---|---|
| ドメインモデル定義書 | ドメインモデル設計書 | [domain-model-design.md](./domain-model-design.md) |
| データベース設計書 | データベース設計書 | [database-design.md](./database-design.md) |
| API仕様書（共通） | API共通仕様 | [api-design/common.md](./api-design/common.md) |
| API仕様書（顧客） | 顧客エンドポイント | [api-design/customers.md](./api-design/customers.md) |
| API仕様書（商品） | 商品エンドポイント | [api-design/products.md](./api-design/products.md) |
| API仕様書（注文） | 注文エンドポイント | [api-design/orders.md](./api-design/orders.md) |
| API仕様書（在庫） | 在庫エンドポイント | [api-design/stocks.md](./api-design/stocks.md) |
| リポジトリ構成 | リポジトリ構造定義書 | [../repository-structure.md](../repository-structure.md) |

---

## 2. システムアーキテクチャ

### レイヤードアーキテクチャ

バックエンドはレイヤードアーキテクチャ（4層構造）を採用する。依存関係は上位層から下位層への一方向のみ許可する。

```
┌─────────────────────────────────────────────────────┐
│  Presentation層（FastAPI）                           │
│  ・HTTPリクエスト/レスポンスの処理                     │
│  ・Pydanticによるリクエストバリデーション              │
│  ・Application層の呼び出し                           │
├─────────────────────────────────────────────────────┤
│  Application層（ユースケース）                        │
│  ・ユースケースの実行順序を制御                        │
│  ・トランザクション境界の管理                          │
│  ・Domain層とInfrastructure層の組み合わせ             │
├─────────────────────────────────────────────────────┤
│  Domain層（ビジネスルール）                           │
│  ・集約・エンティティ・値オブジェクト                  │
│  ・ドメインサービス・ドメインイベント                  │
│  ・リポジトリインターフェース定義                      │
│  ・外部依存なし（純粋なビジネスロジック）              │
├─────────────────────────────────────────────────────┤
│  Infrastructure層（外部連携）                        │
│  ・リポジトリ実装（SQLAlchemy + PostgreSQL）          │
│  ・外部サービス連携                                   │
│  ・環境設定・DB接続                                   │
└─────────────────────────────────────────────────────┘
```

### 技術スタック

| コンポーネント | 採用技術 |
|---|---|
| Webフレームワーク | FastAPI |
| ORM | SQLAlchemy |
| データベース | PostgreSQL 15 |
| マイグレーション | Alembic |
| バリデーション | Pydantic |
| テスト | pytest |

---

## 3. ドメインモデル設計

### 集約一覧

| 集約名 | 集約ルート | 主な値オブジェクト |
|---|---|---|
| 注文集約 | Order | OrderId, OrderStatus, Money |
| 商品集約 | Product | ProductId, SKU, Price |
| 在庫集約 | Stock | StockId, StockQuantity |
| 顧客集約 | Customer | CustomerId, EmailAddress, MemberRank |
| クーポン | Coupon | CouponId, CouponCode, DiscountType |

### ドメインサービス

| サービス名 | 責務 |
|---|---|
| OrderDomainService | 注文作成時の在庫引当・割引計算の調整 |
| DiscountPolicy | 会員ランク → 数量 → クーポンの優先順で割引率を決定 |
| TaxCalculator | 消費税計算 |

### ドメインイベント

| イベント | 発生タイミング |
|---|---|
| OrderPlaced | 注文確定時 |
| OrderCancelled | 注文キャンセル時 |
| OrderShipped | 発送完了時 |
| StockAllocated | 在庫引当時 |
| StockReleased | 在庫解放時 |
| LowStockDetected | 在庫が閾値を下回ったとき |

> 詳細（集約の構造・値オブジェクトの定義・リポジトリインターフェース）は [domain-model-design.md](./domain-model-design.md) を参照。

---

## 4. データベース設計

### テーブル一覧

| テーブル名 | 対応する集約 | 概要 |
|---|---|---|
| `customers` | 顧客集約 | 顧客基本情報 |
| `shipping_addresses` | 顧客集約 | 配送先住所（顧客に紐づく） |
| `products` | 商品集約 | 商品情報 |
| `stocks` | 在庫集約 | 在庫数量・楽観的ロック用バージョン |
| `orders` | 注文集約 | 注文ヘッダー |
| `order_items` | 注文集約 | 注文明細 |
| `coupons` | クーポン | クーポン定義 |
| `domain_events` | - | ドメインイベント（Outboxパターン） |

### ER図（概略）

```
customers ──< shipping_addresses
    │
    ▼
orders ──< order_items >── products ──── stocks
    │
    └──── coupons
```

> 詳細（テーブル定義・カラム型・インデックス・マイグレーション方針）は [database-design.md](./database-design.md) を参照。

---

## 5. API設計

### ベースURL

```
/api/v1
```

### エンドポイント一覧

| メソッド | パス | 概要 | 仕様 |
|---|---|---|---|
| GET | `/customers/{customer_id}` | 顧客情報取得 | [customers.md](./api-design/customers.md) |
| POST | `/customers` | 顧客登録 | [customers.md](./api-design/customers.md) |
| PUT | `/customers/{customer_id}` | 顧客情報更新 | [customers.md](./api-design/customers.md) |
| POST | `/customers/{customer_id}/addresses` | 配送先住所追加 | [customers.md](./api-design/customers.md) |
| GET | `/customers/{customer_id}/orders` | 顧客の注文履歴取得 | [customers.md](./api-design/customers.md) |
| GET | `/products` | 商品一覧取得（フィルタ・ページネーション対応） | [products.md](./api-design/products.md) |
| POST | `/products` | 商品登録 | [products.md](./api-design/products.md) |
| PUT | `/products/{product_id}` | 商品情報更新 | [products.md](./api-design/products.md) |
| DELETE | `/products/{product_id}` | 商品削除 | [products.md](./api-design/products.md) |
| POST | `/orders` | 注文作成 | [orders.md](./api-design/orders.md) |
| GET | `/orders/{order_id}` | 注文詳細取得 | [orders.md](./api-design/orders.md) |
| PUT | `/orders/{order_id}/status` | 注文ステータス更新 | [orders.md](./api-design/orders.md) |
| POST | `/orders/{order_id}/cancel` | 注文キャンセル | [orders.md](./api-design/orders.md) |
| GET | `/stocks/{product_id}` | 在庫情報取得 | [stocks.md](./api-design/stocks.md) |
| PUT | `/stocks/{product_id}` | 在庫数更新 | [stocks.md](./api-design/stocks.md) |

### 共通レスポンス形式

```json
// 成功
{ "data": { ... } }

// 一覧
{ "data": [ ... ], "pagination": { "total": 100, "page": 1, "per_page": 20 } }

// エラー
{ "error": { "code": "ORDER_NOT_FOUND", "message": "..." } }
```

> 詳細（リクエスト/レスポンス定義・エラーコード・処理フロー）は [api-design/common.md](./api-design/common.md) および各エンドポイントのドキュメントを参照。

---

## 6. バックエンドコード構成

### ディレクトリ構造

```
backend/
└── app/
    ├── presentation/          # Presentation層
    │   ├── api/v1/endpoints/  # FastAPI ルーター
    │   └── schemas/           # Pydantic スキーマ（Request / Response）
    ├── application/
    │   └── services/          # ユースケース（アプリケーションサービス）
    ├── domain/
    │   ├── entities/          # エンティティ・集約ルート
    │   ├── value_objects/     # 値オブジェクト
    │   ├── services/          # ドメインサービス
    │   └── repositories/      # リポジトリインターフェース（抽象基底クラス）
    ├── infrastructure/
    │   └── database/
    │       ├── models/        # SQLAlchemy モデル
    │       └── repositories/  # リポジトリ実装
    └── core/                  # DB接続・設定・セキュリティ共通機能
```

### 配置ルール

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

> プロジェクト全体のディレクトリ構成は [repository-structure.md](../repository-structure.md) を参照。

---

## 7. 横断的関心事

### エラーハンドリング方針

| 例外の種類 | 発生層 | HTTPステータス | 説明 |
|---|---|---|---|
| バリデーションエラー | Presentation層（Pydantic） | 400 | リクエストの型・フォーマット不正 |
| ドメイン例外 | Domain層 | 409 | ビジネスルール違反（例: キャンセル済み注文の変更） |
| リソース未検出 | Application層 | 404 | IDに対応するエンティティが存在しない |
| インフラエラー | Infrastructure層 | 500 | DBエラー・外部サービス障害など |

例外はそれぞれの層で定義し、上位層でキャッチして適切なHTTPレスポンスに変換する。Domain層には外部依存の例外クラスを持ち込まない。

### トランザクション境界

トランザクションは **Application層（ユースケース）単位** で管理する。

- 1ユースケース = 1トランザクション
- Domain層はトランザクションを意識しない
- `db.commit()` / `db.rollback()` はApplication層またはInfrastructure層のリポジトリ実装内で呼び出す

```python
# Application層の例
async def execute(self, command: CreateOrderCommand) -> OrderId:
    async with self.unit_of_work:          # トランザクション開始
        order = self.order_domain_service.create_order(...)
        await self.order_repository.save(order)
        await self.unit_of_work.commit()   # コミット
    return order.id
```

### 認証・認可

本システム（OrderHub）の学習用実装では認証は対象外とする。実プロダクトに適用する場合は以下を検討すること。

| 項目 | 方針 |
|---|---|
| 認証方式 | JWT（Bearer トークン）を推奨 |
| 認可 | FastAPI の `Depends()` を使ったミドルウェアで実装 |
| トークン検証 | `presentation/api/deps.py` に集約する |

### ロギング方針

| ログレベル | 用途 |
|---|---|
| INFO | リクエスト受信・ユースケース完了・ドメインイベント発行 |
| WARNING | ビジネスルール違反（ドメイン例外） |
| ERROR | 予期しない例外・インフラエラー |

- リクエストID（`X-Request-ID`）をログに付与し、トレーサビリティを確保する
- ドメイン層にはロガーを持ち込まない。イベントの記録はドメインイベント経由で行う
