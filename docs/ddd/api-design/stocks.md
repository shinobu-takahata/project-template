# 在庫エンドポイント - 注文管理システム（OrderHub）

## GET /api/v1/stocks/{product_id} — 在庫情報取得

### 概要
指定された商品の在庫情報を取得する。

### パスパラメータ
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| product_id | string | 商品ID |

### 処理フロー

**Presentation層**
1. パスパラメータのバリデーション
2. Application層の呼び出し

**Application層（GetStockUseCase）**
1. `StockRepository.find_by_product_id()` で在庫を取得
2. DTOに変換して返却

**Domain層**
- 参照のみ。`available_quantity`（引当可能数）はドメインオブジェクトで算出。

**Infrastructure層**
- SQLAlchemy経由でDBから取得

### レスポンス（200 OK）
```json
{
  "data": {
    "product_id": "prod-001",
    "product_name": "ワイヤレスマウス",
    "quantity": 150,
    "allocated_quantity": 30,
    "available_quantity": 120,
    "low_stock_threshold": 10,
    "is_low_stock": false
  }
}
```

### エラーケース
| エラーコード | 条件 |
|------------|------|
| PRODUCT_NOT_FOUND | 商品IDが存在しない |

---

## PUT /api/v1/stocks/{product_id} — 在庫数更新

### 概要
商品の在庫数を更新する（入荷処理）。

### リクエスト
```json
{
  "additional_quantity": 50,
  "reason": "定期入荷"
}
```

### 処理フロー

**Presentation層**
1. リクエストボディのバリデーション
2. Application層の呼び出し

**Application層（UpdateStockUseCase）**
1. `StockRepository.find_by_product_id()` で在庫を取得
2. `stock.add(quantity)` を呼び出し
3. `StockRepository.save(stock)` で永続化

**Domain層**
- `Stock.add(quantity)`: 在庫数を加算
  - 数量は正の値であること（0以下は `InvalidQuantityError`）

**Infrastructure層**
- SQLAlchemy経由でDB更新

### レスポンス（200 OK）
GET /api/v1/stocks/{product_id} のレスポンスと同一構造。

### エラーケース
| エラーコード | 条件 |
|------------|------|
| PRODUCT_NOT_FOUND | 商品IDが存在しない |
| INVALID_QUANTITY | 数量が0以下 |
