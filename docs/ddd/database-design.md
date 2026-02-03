# データベース設計書 - 注文管理システム（OrderHub）

## データベース構成

### RDBMS
PostgreSQL 15

### スキーマ
`orderhub`（デフォルトスキーマ）

---

## ER図（テキスト表現）

```
customers ──< shipping_addresses
    │
    │
    ▼
orders ──< order_items >── products ──── stocks
    │                         │
    │                         └──< product_categories
    │
    └── coupons
```

---

## テーブル定義

### customers（顧客）

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | VARCHAR(36) | NO | - | 顧客ID（UUID） |
| name | VARCHAR(100) | NO | - | 顧客名 |
| email | VARCHAR(255) | NO | - | メールアドレス |
| member_rank | VARCHAR(20) | NO | 'BRONZE' | 会員ランク（BRONZE/SILVER/GOLD） |
| created_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 更新日時 |

**制約:**
- PK: `id`
- UNIQUE: `email`
- CHECK: `member_rank IN ('BRONZE', 'SILVER', 'GOLD')`

**インデックス:**
- `idx_customers_email` ON `email`

**DDDとの対応:**
- 集約ルート: `Customer`
- 値オブジェクト `MemberRank` → `member_rank` カラムとして永続化

---

### shipping_addresses（配送先住所）

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | VARCHAR(36) | NO | - | 住所ID（UUID） |
| customer_id | VARCHAR(36) | NO | - | 顧客ID（FK） |
| label | VARCHAR(50) | NO | - | ラベル（自宅、会社等） |
| postal_code | VARCHAR(10) | NO | - | 郵便番号 |
| prefecture | VARCHAR(10) | NO | - | 都道府県 |
| city | VARCHAR(100) | NO | - | 市区町村 |
| street | VARCHAR(200) | NO | - | 番地以降 |
| is_default | BOOLEAN | NO | FALSE | デフォルト住所フラグ |
| created_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 更新日時 |

**制約:**
- PK: `id`
- FK: `customer_id` → `customers.id`

**インデックス:**
- `idx_shipping_addresses_customer_id` ON `customer_id`

**DDDとの対応:**
- `Customer` 集約内のエンティティ `ShippingAddress`
- 値オブジェクト `Address` → postal_code, prefecture, city, street の4カラムに展開して永続化
- Customer集約経由でのみアクセスする（リポジトリは `CustomerRepository` のみ）

---

### products（商品）

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | VARCHAR(36) | NO | - | 商品ID（UUID） |
| name | VARCHAR(200) | NO | - | 商品名 |
| sku | VARCHAR(50) | NO | - | SKU（在庫管理単位） |
| price | INTEGER | NO | - | 単価（税抜・円） |
| category | VARCHAR(100) | NO | - | カテゴリ |
| description | TEXT | YES | NULL | 商品説明 |
| deleted_at | TIMESTAMP WITH TIME ZONE | YES | NULL | 論理削除日時 |
| created_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 更新日時 |

**制約:**
- PK: `id`
- UNIQUE: `sku`
- CHECK: `price >= 0`

**インデックス:**
- `idx_products_sku` ON `sku`
- `idx_products_category` ON `category`
- `idx_products_deleted_at` ON `deleted_at` （論理削除フィルタ用）

**DDDとの対応:**
- 集約ルート: `Product`
- 値オブジェクト `Price` → `price` カラム（INTEGER、円単位で保存）
- 値オブジェクト `SKU` → `sku` カラム
- 論理削除は `Product.delete()` で `deleted_at` に値を設定

**金額の扱い:**
- 金額はすべて整数（円単位）で保存する
- ドメイン層では `Money` 値オブジェクトで扱い、通貨演算の精度を保証する
- 税率計算時の端数は切り捨て

---

### stocks（在庫）

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | VARCHAR(36) | NO | - | 在庫ID（UUID） |
| product_id | VARCHAR(36) | NO | - | 商品ID（FK） |
| quantity | INTEGER | NO | 0 | 総在庫数 |
| allocated_quantity | INTEGER | NO | 0 | 引当済み数量 |
| low_stock_threshold | INTEGER | NO | 10 | 在庫少アラート閾値 |
| version | INTEGER | NO | 1 | 楽観的ロック用バージョン |
| created_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 更新日時 |

**制約:**
- PK: `id`
- FK: `product_id` → `products.id`
- UNIQUE: `product_id`
- CHECK: `quantity >= 0`
- CHECK: `allocated_quantity >= 0`
- CHECK: `allocated_quantity <= quantity`

**インデックス:**
- `idx_stocks_product_id` ON `product_id`

**DDDとの対応:**
- 集約ルート: `Stock`
- 引当可能数 = `quantity - allocated_quantity`（ドメイン層で算出、DBには保存しない）
- `version` カラムで楽観的ロックを実現（同時注文による在庫競合の防止）
- `Stock.allocate()` → `allocated_quantity` を加算
- `Stock.release()` → `allocated_quantity` を減算

**楽観的ロック:**
```sql
UPDATE stocks
SET allocated_quantity = allocated_quantity + :qty,
    version = version + 1,
    updated_at = CURRENT_TIMESTAMP
WHERE id = :id AND version = :current_version;
-- affected_rows == 0 の場合は OptimisticLockError
```

---

### orders（注文）

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | VARCHAR(36) | NO | - | 注文ID（UUID） |
| order_number | VARCHAR(30) | NO | - | 注文番号（表示用） |
| customer_id | VARCHAR(36) | NO | - | 顧客ID（FK） |
| status | VARCHAR(20) | NO | 'CONFIRMED' | 注文ステータス |
| subtotal | INTEGER | NO | - | 小計（税抜・円） |
| discount_amount | INTEGER | NO | 0 | 割引額（円） |
| tax_amount | INTEGER | NO | - | 税額（円） |
| shipping_fee | INTEGER | NO | 0 | 送料（円） |
| total_amount | INTEGER | NO | - | 合計金額（税込・円） |
| shipping_postal_code | VARCHAR(10) | NO | - | 配送先郵便番号 |
| shipping_prefecture | VARCHAR(10) | NO | - | 配送先都道府県 |
| shipping_city | VARCHAR(100) | NO | - | 配送先市区町村 |
| shipping_street | VARCHAR(200) | NO | - | 配送先番地以降 |
| coupon_code | VARCHAR(50) | YES | NULL | 適用クーポンコード |
| cancel_reason | TEXT | YES | NULL | キャンセル理由 |
| ordered_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 注文日時 |
| cancelled_at | TIMESTAMP WITH TIME ZONE | YES | NULL | キャンセル日時 |
| created_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 更新日時 |

**制約:**
- PK: `id`
- UNIQUE: `order_number`
- FK: `customer_id` → `customers.id`
- CHECK: `status IN ('CONFIRMED', 'PAID', 'PREPARING', 'SHIPPED', 'DELIVERED', 'CANCELLED')`
- CHECK: `subtotal >= 0`
- CHECK: `total_amount >= 0`

**インデックス:**
- `idx_orders_order_number` ON `order_number`
- `idx_orders_customer_id` ON `customer_id`
- `idx_orders_status` ON `status`
- `idx_orders_ordered_at` ON `ordered_at`

**DDDとの対応:**
- 集約ルート: `Order`
- 値オブジェクト `OrderStatus` → `status` カラム
- 値オブジェクト `Money` → subtotal, discount_amount, tax_amount, shipping_fee, total_amount の各カラム
- 値オブジェクト `Address` → shipping_postal_code, shipping_prefecture, shipping_city, shipping_street に展開
  - 注文時点の住所をスナップショットとして保存（顧客の住所変更の影響を受けない）
- ステータス遷移はドメイン層 `Order.transition_to()` で制御（DBのCHECK制約は最終防衛線）

---

### order_items（注文明細）

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | VARCHAR(36) | NO | - | 明細ID（UUID） |
| order_id | VARCHAR(36) | NO | - | 注文ID（FK） |
| product_id | VARCHAR(36) | NO | - | 商品ID（FK） |
| product_name | VARCHAR(200) | NO | - | 商品名（注文時スナップショット） |
| unit_price | INTEGER | NO | - | 単価（注文時スナップショット・円） |
| quantity | INTEGER | NO | - | 数量 |
| subtotal | INTEGER | NO | - | 小計（円） |
| created_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 作成日時 |

**制約:**
- PK: `id`
- FK: `order_id` → `orders.id` ON DELETE CASCADE
- FK: `product_id` → `products.id`
- CHECK: `quantity > 0`
- CHECK: `unit_price >= 0`

**インデックス:**
- `idx_order_items_order_id` ON `order_id`
- `idx_order_items_product_id` ON `product_id`

**DDDとの対応:**
- `Order` 集約内のエンティティ `OrderItem`
- `product_name` と `unit_price` は注文時点のスナップショット（商品マスタの変更に影響されない）
- Order集約経由でのみアクセスする（専用のリポジトリは持たない）

---

### coupons（クーポン）

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | VARCHAR(36) | NO | - | クーポンID（UUID） |
| code | VARCHAR(50) | NO | - | クーポンコード |
| discount_type | VARCHAR(20) | NO | - | 割引種別（FIXED/PERCENTAGE） |
| discount_value | INTEGER | NO | - | 割引値（FIXEDは円、PERCENTAGEは%） |
| min_order_amount | INTEGER | NO | 0 | 最低注文金額（円） |
| max_usage_count | INTEGER | YES | NULL | 最大利用回数（NULLは無制限） |
| current_usage_count | INTEGER | NO | 0 | 現在の利用回数 |
| valid_from | TIMESTAMP WITH TIME ZONE | NO | - | 有効開始日時 |
| valid_until | TIMESTAMP WITH TIME ZONE | NO | - | 有効終了日時 |
| is_active | BOOLEAN | NO | TRUE | 有効フラグ |
| created_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 更新日時 |

**制約:**
- PK: `id`
- UNIQUE: `code`
- CHECK: `discount_type IN ('FIXED', 'PERCENTAGE')`
- CHECK: `discount_value > 0`
- CHECK: `valid_from < valid_until`

**インデックス:**
- `idx_coupons_code` ON `code`

**DDDとの対応:**
- 割引ポリシーの一部として利用
- クーポンの有効性判定はドメインサービス `DiscountPolicy` 内で実施

---

### domain_events（ドメインイベント）

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | VARCHAR(36) | NO | - | イベントID（UUID） |
| event_type | VARCHAR(100) | NO | - | イベント種別 |
| aggregate_type | VARCHAR(50) | NO | - | 集約種別 |
| aggregate_id | VARCHAR(36) | NO | - | 集約ID |
| payload | JSONB | NO | - | イベントデータ |
| occurred_at | TIMESTAMP WITH TIME ZONE | NO | CURRENT_TIMESTAMP | 発生日時 |
| published | BOOLEAN | NO | FALSE | 発行済みフラグ |

**制約:**
- PK: `id`

**インデックス:**
- `idx_domain_events_aggregate` ON `aggregate_type, aggregate_id`
- `idx_domain_events_published` ON `published` WHERE `published = FALSE`
- `idx_domain_events_occurred_at` ON `occurred_at`

**DDDとの対応:**
- ドメインイベントの永続化用テーブル（Outboxパターン）
- `OrderPlaced`, `OrderCancelled`, `OrderShipped`, `StockAllocated`, `StockReleased`, `LowStockDetected` 等を保存
- 将来的な非同期処理やイベント駆動連携の基盤

---

## マイグレーション方針

- Alembic を使用してマイグレーションを管理する
- 各テーブルの `created_at`, `updated_at` はアプリケーション側で設定する（SQLAlchemyイベントフック）
- UUIDはアプリケーション側（ドメイン層）で生成する

## データ型の設計判断

| 概念 | DB型 | 理由 |
|------|------|------|
| ID | VARCHAR(36) | UUID文字列。ドメイン層でID生成を制御するため |
| 金額 | INTEGER | 円単位の整数。浮動小数点の誤差を回避 |
| ステータス | VARCHAR(20) | ENUMではなくVARCHARを使用。マイグレーションの柔軟性を確保 |
| タイムスタンプ | TIMESTAMP WITH TIME ZONE | タイムゾーン情報を保持 |
| イベントデータ | JSONB | スキーマレスなイベントペイロードを柔軟に保存 |
