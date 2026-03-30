# 詳細設計書 - POST /api/v1/orders — 注文作成

## 基本情報

| 項目 | 内容 |
|---|---|
| エンドポイント | `POST /api/v1/orders` |
| ユースケースクラス | `CreateOrderUseCase` |
| 発行するドメインイベント | `OrderPlaced`、`StockAllocated` |
| トランザクション | あり（`orders` テーブルと `stocks` テーブルの同時更新） |
| 処理フロー（レイヤー別） | → [api-design/orders.md](../api-design/orders.md#post-apiv1orders--注文作成) |
| エラーハンドリング方針 | → [backend-detailed-design.md § 7](../backend-detailed-design.md#エラーハンドリング方針) |
| トランザクション方針 | → [backend-detailed-design.md § 7](../backend-detailed-design.md#トランザクション境界) |
| リポジトリ構成 | → [backend-detailed-design.md § 6](../backend-detailed-design.md#6-バックエンドコード構成リポジトリ構成) |
| ロギング方針 | → [backend-detailed-design.md § 7](../backend-detailed-design.md#ロギング方針) |

---

## 概要

カートの内容をもとに注文を作成する。在庫引当・割引計算・合計金額算出を行い、注文を `CONFIRMED` ステータスで確定する。

---

## 事前条件・事後条件

### 事前条件

- 指定した `customer_id` の顧客が存在すること
- 指定した `shipping_address_id` が当該顧客に紐づいていること
- 指定した全 `product_id` の商品が存在すること
- 各商品の引当可能在庫数（`available_quantity`）が注文数量以上であること

### 事後条件

- `orders` テーブルにステータス `CONFIRMED` のレコードが1件作成されること
- `order_items` テーブルに注文明細レコードが商品数分作成されること
- `stocks` テーブルの各商品の `allocated_quantity` が注文数量分増加すること
- `domain_events` テーブルに `OrderPlaced` イベントが記録されること

テーブル定義 → [database-design.md](../database-design.md)

---

## インターフェース定義

### リクエストボディ

| フィールド | 型 | 必須 | バリデーション |
|---|---|---|---|
| `customer_id` | string | Yes | UUID形式 |
| `shipping_address_id` | string | Yes | UUID形式 |
| `items` | array | Yes | 1件以上、要素の重複不可（同一 `product_id` が2件以上あってはならない） |
| `items[].product_id` | string | Yes | UUID形式 |
| `items[].quantity` | integer | Yes | 1以上の整数 |
| `coupon_code` | string | No | 英数字・ハイフンのみ、最大20文字 |

```json
{
  "customer_id": "cust-001",
  "shipping_address_id": "addr-001",
  "items": [
    { "product_id": "prod-001", "quantity": 3 },
    { "product_id": "prod-002", "quantity": 1 }
  ],
  "coupon_code": "SPRING2026"
}
```

### レスポンスボディ（201 Created）

リクエスト/レスポンスのサンプルJSON → [api-design/orders.md](../api-design/orders.md#post-apiv1orders--注文作成)

| フィールド | 型 | 説明 |
|---|---|---|
| `order_id` | string | 採番された注文ID（`ord-YYYYMMDD-NNN` 形式） |
| `status` | string | 常に `CONFIRMED` |
| `items[].product_name` | string | 注文確定時点の商品名（スナップショット。以降の商品名変更の影響を受けない） |
| `items[].unit_price` | integer | 注文確定時点の単価（税抜、円） |
| `subtotal` | integer | 割引・税・送料を除いた合計（税抜） |
| `discount_amount` | integer | 全割引の合計額 |
| `tax_amount` | integer | 消費税額（税率10%） |
| `shipping_fee` | integer | 送料（無料条件は下記ビジネスルール参照） |
| `total_amount` | integer | 最終請求額（`subtotal - discount_amount + tax_amount + shipping_fee`） |
| `shipping_address` | object | 注文確定時点の配送先スナップショット |
| `ordered_at` | string | ISO 8601形式、タイムゾーン付き |

---

## ビジネスルール

> 各ルールの詳細なドメインロジックは [domain-model-design.md](../domain-model-design.md) を参照。

1. **在庫引当**: `Stock.allocate(quantity)` を呼び出す。`available_quantity（= quantity - allocated_quantity）` が不足する場合は `InsufficientStockError`。

2. **割引の適用順序**（`DiscountPolicy.apply()`）:
   1. 会員ランク割引を小計に適用（BRONZE: 0%, SILVER: 5%, GOLD: 10%）
   2. 数量割引を対象商品に適用（同一商品5個以上: 3%）
   3. クーポン割引を最終合計に適用

3. **送料**: 割引後の小計が5,000円以上で送料無料、未満は一律500円。

4. **配送先スナップショット**: 注文確定時の住所情報を `orders.shipping_address_*` カラムに直接保存する。以降の顧客住所変更の影響を受けない。

5. **商品名・単価スナップショット**: `order_items` の `product_name`・`unit_price` は注文確定時点の値を保存する。以降の商品情報変更の影響を受けない。

6. **注文番号採番**: `ord-YYYYMMDD-NNN`（NNNはその日の連番、ゼロ埋め3桁）。

---

## エラーケース

| エラーコード | HTTP | 条件 |
|---|---|---|
| `VALIDATION_ERROR` | 400 | リクエスト形式不正（型・必須・フォーマット違反） |
| `CUSTOMER_NOT_FOUND` | 404 | `customer_id` が存在しない |
| `PRODUCT_NOT_FOUND` | 404 | `items[].product_id` のいずれかが存在しない |
| `INVALID_SHIPPING_ADDRESS` | 409 | `shipping_address_id` が当該顧客に紐づいていない |
| `INSUFFICIENT_STOCK` | 409 | 在庫の引当可能数が注文数量を下回る |
| `INVALID_COUPON` | 409 | クーポンが存在しない、無効、または期限切れ |

```json
// 400 VALIDATION_ERROR
{
  "error": { "code": "VALIDATION_ERROR", "message": "items は1件以上指定してください" }
}

// 404 PRODUCT_NOT_FOUND
{
  "error": { "code": "PRODUCT_NOT_FOUND", "message": "商品が見つかりません: prod-999" }
}

// 409 INVALID_SHIPPING_ADDRESS
{
  "error": { "code": "INVALID_SHIPPING_ADDRESS", "message": "指定の配送先住所は当該顧客に紐づいていません" }
}

// 409 INSUFFICIENT_STOCK
{
  "error": { "code": "INSUFFICIENT_STOCK", "message": "在庫が不足しています: prod-001 (要求: 10, 引当可能: 5)" }
}

// 409 INVALID_COUPON
{
  "error": { "code": "INVALID_COUPON", "message": "クーポンが無効または期限切れです: SPRING2026" }
}
```

---

