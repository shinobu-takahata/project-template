# 注文エンドポイント - 注文管理システム（OrderHub）

## POST /api/v1/orders — 注文作成

### 概要
カートの内容をもとに注文を作成する。在庫引当・割引計算・合計金額算出を行う。

### リクエスト
```json
{
  "customer_id": "cust-001",
  "shipping_address_id": "addr-001",
  "items": [
    {
      "product_id": "prod-001",
      "quantity": 3
    },
    {
      "product_id": "prod-002",
      "quantity": 1
    }
  ],
  "coupon_code": "SPRING2026"
}
```

### 処理フロー（レイヤー別）

**Presentation層（Router）**
1. リクエストボディのバリデーション（Pydanticスキーマ）
2. Application層のユースケースを呼び出し
3. レスポンスのシリアライズ

**Application層（CreateOrderUseCase）**
1. `CustomerRepository.find_by_id()` で顧客を取得（存在しなければ404）
2. 顧客の配送先住所を検証
3. `ProductRepository.find_by_ids()` で商品情報を一括取得
4. 各商品について `StockRepository.find_by_product_id()` で在庫を取得
5. ドメインサービス `OrderDomainService.create_order()` を呼び出し
6. トランザクション内で以下を永続化:
   - `OrderRepository.save(order)`
   - `StockRepository.save(stock)` （引当後の在庫）
7. ドメインイベント `OrderPlaced` を発行

**Domain層**
- `Order.create()`: 注文を生成し、注文明細を追加
- `Stock.allocate(quantity)`: 在庫を引当（不足時は `InsufficientStockError`）
- `DiscountPolicy.apply()`: 割引ルールを順に適用
  1. 会員ランク割引を小計に適用
  2. 数量割引を該当商品に適用
  3. クーポン割引を最終合計に適用
- `Money`: 金額計算（税込計算含む）

**Infrastructure層**
- SQLAlchemy経由でDB永続化
- ドメインイベントの発行（インメモリイベントバス）

### レスポンス（201 Created）
```json
{
  "data": {
    "order_id": "ord-20260203-001",
    "status": "CONFIRMED",
    "customer_id": "cust-001",
    "items": [
      {
        "product_id": "prod-001",
        "product_name": "ワイヤレスマウス",
        "unit_price": 3000,
        "quantity": 3,
        "subtotal": 9000
      },
      {
        "product_id": "prod-002",
        "product_name": "USBケーブル",
        "unit_price": 500,
        "quantity": 1,
        "subtotal": 500
      }
    ],
    "subtotal": 9500,
    "discount_amount": 950,
    "tax_amount": 855,
    "shipping_fee": 500,
    "total_amount": 9905,
    "shipping_address": {
      "postal_code": "100-0001",
      "prefecture": "東京都",
      "city": "千代田区",
      "street": "千代田1-1-1"
    },
    "ordered_at": "2026-02-03T10:00:00+09:00"
  }
}
```

### エラーケース
| エラーコード | 条件 |
|------------|------|
| CUSTOMER_NOT_FOUND | 顧客IDが存在しない |
| PRODUCT_NOT_FOUND | 商品IDが存在しない |
| INSUFFICIENT_STOCK | 在庫不足 |
| INVALID_COUPON | クーポンが無効または期限切れ |
| INVALID_SHIPPING_ADDRESS | 指定の配送先住所が顧客に紐付いていない |

---

## GET /api/v1/orders/{order_id} — 注文詳細取得

### 概要
指定された注文の詳細情報を取得する。

### パスパラメータ
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| order_id | string | 注文ID |

### 処理フロー

**Presentation層**
1. パスパラメータのバリデーション
2. Application層の呼び出し

**Application層（GetOrderUseCase）**
1. `OrderRepository.find_by_id()` で注文を取得
2. 存在しなければ `OrderNotFoundError`
3. DTOに変換して返却

**Domain層**
- 参照のみ。ドメインロジックは発動しない。

**Infrastructure層**
- SQLAlchemy経由でDBから取得
- 注文明細はOrder集約内でEager Loadingで取得

### レスポンス（200 OK）
POST /api/v1/orders のレスポンスと同一構造。`status` が現在のステータスを反映する。

### エラーケース
| エラーコード | 条件 |
|------------|------|
| ORDER_NOT_FOUND | 注文IDが存在しない |

---

## PUT /api/v1/orders/{order_id}/status — 注文ステータス更新

### 概要
注文のステータスを次の状態に遷移させる。不正な遷移はドメイン層で拒否される。

### リクエスト
```json
{
  "status": "PAID"
}
```

### 処理フロー

**Presentation層**
1. リクエストボディのバリデーション（有効なステータス値か）
2. Application層の呼び出し

**Application層（UpdateOrderStatusUseCase）**
1. `OrderRepository.find_by_id()` で注文を取得
2. `order.transition_to(new_status)` を呼び出し
3. `OrderRepository.save(order)` で永続化
4. ステータスに応じたドメインイベントを発行
   - SHIPPED → `OrderShipped` イベント

**Domain層**
- `Order.transition_to(status)`: 状態遷移の妥当性を検証
  - 許可される遷移:
    - CONFIRMED → PAID
    - PAID → PREPARING
    - PREPARING → SHIPPED
    - SHIPPED → DELIVERED
  - 上記以外の遷移は `InvalidStatusTransitionError`
- `OrderStatus`: 遷移可能なステータスのマッピングを保持する値オブジェクト

**Infrastructure層**
- SQLAlchemy経由で更新

### レスポンス（200 OK）
```json
{
  "data": {
    "order_id": "ord-20260203-001",
    "previous_status": "CONFIRMED",
    "current_status": "PAID",
    "updated_at": "2026-02-03T11:00:00+09:00"
  }
}
```

### エラーケース
| エラーコード | 条件 |
|------------|------|
| ORDER_NOT_FOUND | 注文IDが存在しない |
| INVALID_STATUS_TRANSITION | 許可されないステータス遷移 |

---

## POST /api/v1/orders/{order_id}/cancel — 注文キャンセル

### 概要
注文をキャンセルする。キャンセル可能なステータス（CONFIRMED, PAID, PREPARING）の場合のみ受け付ける。在庫の戻しも行う。

### リクエスト
```json
{
  "reason": "注文を間違えたため"
}
```

### 処理フロー

**Presentation層**
1. リクエストボディのバリデーション
2. Application層の呼び出し

**Application層（CancelOrderUseCase）**
1. `OrderRepository.find_by_id()` で注文を取得
2. `order.cancel(reason)` を呼び出し
3. 注文明細の各商品について `StockRepository.find_by_product_id()` で在庫を取得
4. `stock.release(quantity)` で在庫を戻す
5. トランザクション内で以下を永続化:
   - `OrderRepository.save(order)`
   - `StockRepository.save(stock)`
6. ドメインイベント `OrderCancelled` を発行

**Domain層**
- `Order.cancel(reason)`: キャンセル可否を判定
  - CONFIRMED, PAID, PREPARING → キャンセル可（ステータスをCANCELLEDに変更）
  - SHIPPED, DELIVERED → `OrderCannotBeCancelledError`
- `Stock.release(quantity)`: 引当済み在庫を戻す

**Infrastructure層**
- SQLAlchemy経由でDB更新
- `OrderCancelled` イベント発行

### レスポンス（200 OK）
```json
{
  "data": {
    "order_id": "ord-20260203-001",
    "status": "CANCELLED",
    "cancel_reason": "注文を間違えたため",
    "cancelled_at": "2026-02-03T12:00:00+09:00"
  }
}
```

### エラーケース
| エラーコード | 条件 |
|------------|------|
| ORDER_NOT_FOUND | 注文IDが存在しない |
| ORDER_CANNOT_BE_CANCELLED | 出荷済み/配達完了の注文 |
