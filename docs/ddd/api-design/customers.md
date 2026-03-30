# 顧客エンドポイント - 注文管理システム（OrderHub）

## GET /api/v1/customers/{customer_id} — 顧客情報取得

### 概要
顧客の基本情報と配送先住所一覧を取得する。

### 処理フロー

**Presentation層**
1. パスパラメータのバリデーション
2. Application層の呼び出し

**Application層（GetCustomerUseCase）**
1. `CustomerRepository.find_by_id()` で顧客を取得（配送先住所含む）
2. DTOに変換して返却

**Domain層**
- 参照のみ。

**Infrastructure層**
- SQLAlchemy経由でDBから取得（配送先住所はCustomer集約内でEager Loading）

### レスポンス（200 OK）
```json
{
  "data": {
    "customer_id": "cust-001",
    "name": "田中太郎",
    "email": "tanaka@example.com",
    "member_rank": "GOLD",
    "shipping_addresses": [
      {
        "address_id": "addr-001",
        "label": "自宅",
        "postal_code": "100-0001",
        "prefecture": "東京都",
        "city": "千代田区",
        "street": "千代田1-1-1",
        "is_default": true
      },
      {
        "address_id": "addr-002",
        "label": "会社",
        "postal_code": "150-0001",
        "prefecture": "東京都",
        "city": "渋谷区",
        "street": "渋谷2-2-2",
        "is_default": false
      }
    ],
    "created_at": "2025-01-01T00:00:00+09:00"
  }
}
```

### エラーケース
| エラーコード | 条件 |
|------------|------|
| CUSTOMER_NOT_FOUND | 顧客IDが存在しない |

---

## POST /api/v1/customers — 顧客登録

### 概要
新しい顧客を登録する。

### リクエスト
```json
{
  "name": "田中太郎",
  "email": "tanaka@example.com",
  "shipping_address": {
    "label": "自宅",
    "postal_code": "100-0001",
    "prefecture": "東京都",
    "city": "千代田区",
    "street": "千代田1-1-1"
  }
}
```

### 処理フロー

**Presentation層**
1. リクエストボディのバリデーション
2. Application層の呼び出し

**Application層（RegisterCustomerUseCase）**
1. `CustomerRepository.find_by_email()` でメールアドレス重複チェック
2. `Customer.create()` でドメインオブジェクトを生成（初期ランクはBRONZE）
3. `customer.add_shipping_address()` でデフォルト配送先を追加
4. `CustomerRepository.save(customer)` で永続化

**Domain層**
- `Customer.create(name, email)`: 顧客を生成（MemberRankはBRONZEで初期化）
- `Customer.add_shipping_address(address)`: 配送先住所を追加
- `Address`: 値オブジェクトとして郵便番号等のフォーマットを検証

**Infrastructure層**
- SQLAlchemy経由でDB永続化

### レスポンス（201 Created）
GET /api/v1/customers/{customer_id} のレスポンスと同一構造。

### エラーケース
| エラーコード | 条件 |
|------------|------|
| DUPLICATE_EMAIL | メールアドレスが既に登録済み |
| INVALID_ADDRESS | 住所のフォーマットが不正 |

---

## PUT /api/v1/customers/{customer_id} — 顧客情報更新

### 概要
顧客の基本情報を更新する。

### リクエスト
```json
{
  "name": "田中太郎",
  "email": "tanaka-new@example.com"
}
```

### 処理フロー

**Presentation層**
1. リクエストボディのバリデーション
2. Application層の呼び出し

**Application層（UpdateCustomerUseCase）**
1. `CustomerRepository.find_by_id()` で顧客を取得
2. メールアドレス変更時は `CustomerRepository.find_by_email()` で重複チェック
3. `customer.update(name, email)` を呼び出し
4. `CustomerRepository.save(customer)` で永続化

**Domain層**
- `Customer.update()`: 顧客情報を更新

**Infrastructure層**
- SQLAlchemy経由でDB更新

### レスポンス（200 OK）
GET /api/v1/customers/{customer_id} のレスポンスと同一構造。

### エラーケース
| エラーコード | 条件 |
|------------|------|
| CUSTOMER_NOT_FOUND | 顧客IDが存在しない |
| DUPLICATE_EMAIL | メールアドレスが既に登録済み |

---

## POST /api/v1/customers/{customer_id}/addresses — 配送先住所追加

### 概要
顧客に新しい配送先住所を追加する。

### リクエスト
```json
{
  "label": "会社",
  "postal_code": "150-0001",
  "prefecture": "東京都",
  "city": "渋谷区",
  "street": "渋谷2-2-2",
  "is_default": false
}
```

### 処理フロー

**Presentation層**
1. リクエストボディのバリデーション
2. Application層の呼び出し

**Application層（AddShippingAddressUseCase）**
1. `CustomerRepository.find_by_id()` で顧客を取得
2. `customer.add_shipping_address(address)` を呼び出し
3. `CustomerRepository.save(customer)` で永続化

**Domain層**
- `Customer.add_shipping_address()`: 配送先を追加
  - 最大5件まで（超過時は `MaxAddressLimitExceededError`）
  - `is_default=true` の場合、既存のデフォルトを解除

**Infrastructure層**
- SQLAlchemy経由でDB永続化

### レスポンス（201 Created）
```json
{
  "data": {
    "address_id": "addr-003",
    "label": "会社",
    "postal_code": "150-0001",
    "prefecture": "東京都",
    "city": "渋谷区",
    "street": "渋谷2-2-2",
    "is_default": false
  }
}
```

### エラーケース
| エラーコード | 条件 |
|------------|------|
| CUSTOMER_NOT_FOUND | 顧客IDが存在しない |
| MAX_ADDRESS_LIMIT | 配送先住所が5件を超える |
| INVALID_ADDRESS | 住所のフォーマットが不正 |

---

## GET /api/v1/customers/{customer_id}/orders — 顧客注文履歴取得

### 概要
指定された顧客の注文履歴を取得する。

### クエリパラメータ
| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| status | string | No | - | ステータスでフィルタ |
| page | int | No | 1 | ページ番号 |
| per_page | int | No | 20 | 1ページあたりの件数 |

### 処理フロー

**Presentation層**
1. クエリパラメータのバリデーション
2. Application層の呼び出し

**Application層（ListCustomerOrdersUseCase）**
1. `CustomerRepository.find_by_id()` で顧客の存在確認
2. `OrderRepository.find_by_customer_id(customer_id, status, page, per_page)` で注文一覧を取得
3. DTOに変換して返却

**Domain層**
- 参照のみ。

**Infrastructure層**
- SQLAlchemy経由でDBから取得（ページネーション付き）

### レスポンス（200 OK）
```json
{
  "data": [
    {
      "order_id": "ord-20260203-001",
      "status": "DELIVERED",
      "total_amount": 9905,
      "item_count": 2,
      "ordered_at": "2026-02-03T10:00:00+09:00"
    }
  ],
  "pagination": {
    "total": 5,
    "page": 1,
    "per_page": 20
  }
}
```

### エラーケース
| エラーコード | 条件 |
|------------|------|
| CUSTOMER_NOT_FOUND | 顧客IDが存在しない |
