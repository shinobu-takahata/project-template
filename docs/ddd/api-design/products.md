# 商品エンドポイント - 注文管理システム（OrderHub）

## GET /api/v1/products — 商品一覧取得

### 概要
商品の一覧を取得する。カテゴリでのフィルタリングとページネーションに対応する。

### クエリパラメータ
| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| category | string | No | - | カテゴリでフィルタ |
| page | int | No | 1 | ページ番号 |
| per_page | int | No | 20 | 1ページあたりの件数（最大100） |

### 処理フロー

**Presentation層**
1. クエリパラメータのバリデーション
2. Application層の呼び出し

**Application層（ListProductsUseCase）**
1. `ProductRepository.find_all(category, page, per_page)` で商品一覧を取得
2. DTOに変換して返却

**Domain層**
- 参照のみ。ドメインロジックは発動しない。

**Infrastructure層**
- SQLAlchemy経由でDBから取得（ページネーション付き）

### レスポンス（200 OK）
```json
{
  "data": [
    {
      "product_id": "prod-001",
      "name": "ワイヤレスマウス",
      "sku": "WM-001",
      "price": 3000,
      "category": "PC周辺機器",
      "stock_quantity": 150
    }
  ],
  "pagination": {
    "total": 45,
    "page": 1,
    "per_page": 20
  }
}
```

---

## POST /api/v1/products — 商品登録

### 概要
新しい商品を登録する。

### リクエスト
```json
{
  "name": "ワイヤレスマウス",
  "sku": "WM-001",
  "price": 3000,
  "category": "PC周辺機器",
  "description": "Bluetooth対応ワイヤレスマウス",
  "initial_stock": 100
}
```

### 処理フロー

**Presentation層**
1. リクエストボディのバリデーション
2. Application層の呼び出し

**Application層（RegisterProductUseCase）**
1. `ProductRepository.find_by_sku()` でSKU重複チェック
2. `Product.create()` でドメインオブジェクトを生成
3. `Stock.initialize()` で初期在庫を生成
4. トランザクション内で永続化:
   - `ProductRepository.save(product)`
   - `StockRepository.save(stock)`

**Domain層**
- `Product.create(name, sku, price, category)`: 商品を生成
  - SKUのフォーマット検証（値オブジェクト `SKU` で実施）
  - 価格が0以上であることの検証（値オブジェクト `Price` で実施）
- `Stock.initialize(product_id, quantity)`: 初期在庫を生成

**Infrastructure層**
- SQLAlchemy経由でDB永続化

### レスポンス（201 Created）
```json
{
  "data": {
    "product_id": "prod-001",
    "name": "ワイヤレスマウス",
    "sku": "WM-001",
    "price": 3000,
    "category": "PC周辺機器",
    "description": "Bluetooth対応ワイヤレスマウス",
    "stock_quantity": 100,
    "created_at": "2026-02-03T10:00:00+09:00"
  }
}
```

### エラーケース
| エラーコード | 条件 |
|------------|------|
| DUPLICATE_SKU | SKUが既に存在する |
| INVALID_PRICE | 価格が負の値 |
| INVALID_SKU_FORMAT | SKUのフォーマットが不正 |

---

## PUT /api/v1/products/{product_id} — 商品更新

### 概要
既存の商品情報を更新する。

### リクエスト
```json
{
  "name": "ワイヤレスマウス Pro",
  "price": 4500,
  "category": "PC周辺機器",
  "description": "Bluetooth 5.0対応 高精度ワイヤレスマウス"
}
```

### 処理フロー

**Presentation層**
1. リクエストボディのバリデーション
2. Application層の呼び出し

**Application層（UpdateProductUseCase）**
1. `ProductRepository.find_by_id()` で商品を取得
2. `product.update(name, price, category, description)` を呼び出し
3. `ProductRepository.save(product)` で永続化

**Domain層**
- `Product.update()`: 商品情報を更新
  - 価格変更時は値オブジェクト `Price` で妥当性を検証

**Infrastructure層**
- SQLAlchemy経由でDB更新

### レスポンス（200 OK）
POST /api/v1/products のレスポンスと同一構造。

### エラーケース
| エラーコード | 条件 |
|------------|------|
| PRODUCT_NOT_FOUND | 商品IDが存在しない |
| INVALID_PRICE | 価格が負の値 |

---

## DELETE /api/v1/products/{product_id} — 商品削除

### 概要
商品を論理削除する。未完了の注文に含まれる商品は削除できない。

### 処理フロー

**Presentation層**
1. パスパラメータのバリデーション
2. Application層の呼び出し

**Application層（DeleteProductUseCase）**
1. `ProductRepository.find_by_id()` で商品を取得
2. `OrderRepository.exists_active_order_with_product(product_id)` で未完了注文チェック
3. 未完了注文が存在する場合は `ProductInUseError`
4. `product.delete()` を呼び出し（論理削除）
5. `ProductRepository.save(product)` で永続化

**Domain層**
- `Product.delete()`: 削除フラグを立てる

**Infrastructure層**
- SQLAlchemy経由でDB更新（`deleted_at` に日時を設定）

### レスポンス（204 No Content）
ボディなし。

### エラーケース
| エラーコード | 条件 |
|------------|------|
| PRODUCT_NOT_FOUND | 商品IDが存在しない |
| PRODUCT_IN_USE | 未完了の注文に含まれている |
