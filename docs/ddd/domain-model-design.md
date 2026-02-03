# ドメインモデル設計書 - 注文管理システム（OrderHub）

## 概要
本ドキュメントでは、注文管理システムのドメインモデルを定義する。
DDDの戦術的パターン（集約、エンティティ、値オブジェクト、ドメインサービス、ドメインイベント、リポジトリ）の適用方針を示す。

---

## 境界づけられたコンテキスト

本システムは単一の境界づけられたコンテキスト「注文管理コンテキスト」として構成する。
学習用プロジェクトのため、コンテキスト間の連携（コンテキストマップ）は扱わない。

```
┌─────────────────────────────────────────────┐
│           注文管理コンテキスト                  │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 注文集約  │  │ 商品集約  │  │ 在庫集約  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│  ┌──────────┐  ┌──────────┐               │
│  │ 顧客集約  │  │ クーポン  │               │
│  └──────────┘  └──────────┘               │
└─────────────────────────────────────────────┘
```

---

## 集約一覧

| 集約名 | 集約ルート | 集約内エンティティ | 主な値オブジェクト |
|-------|----------|----------------|----------------|
| 注文集約 | Order | OrderItem | OrderId, OrderStatus, Money, Quantity |
| 商品集約 | Product | - | ProductId, ProductName, SKU, Price |
| 在庫集約 | Stock | - | StockId, StockQuantity |
| 顧客集約 | Customer | ShippingAddress | CustomerId, CustomerName, EmailAddress, MemberRank, Address |
| クーポン | Coupon | - | CouponId, CouponCode, DiscountType |

---

## 注文集約（Order Aggregate）

### 集約ルート: Order

注文のライフサイクル全体を管理する。注文明細（OrderItem）は Order 集約内のエンティティとして管理し、必ず Order 経由で操作する。

```
Order (集約ルート)
├── id: OrderId
├── order_number: OrderNumber
├── customer_id: CustomerId        ※他集約へのIDによる参照
├── status: OrderStatus
├── items: List[OrderItem]         ※集約内エンティティ
├── subtotal: Money
├── discount_amount: Money
├── tax_amount: Money
├── shipping_fee: Money
├── total_amount: Money
├── shipping_address: Address      ※注文時点のスナップショット
├── coupon_code: Optional[CouponCode]
├── cancel_reason: Optional[str]
├── ordered_at: datetime
└── cancelled_at: Optional[datetime]
```

#### ファクトリメソッド

```python
@staticmethod
def create(
    customer_id: CustomerId,
    items: List[Tuple[Product, Quantity]],
    shipping_address: Address,
    discount_amount: Money,
    coupon_code: Optional[CouponCode] = None,
) -> "Order":
    """
    注文を生成する。
    - OrderIdを採番
    - OrderNumberを生成（例: ord-20260203-001）
    - 各商品からOrderItemを生成
    - 小計・税額・合計を算出
    - ステータスをCONFIRMEDに設定
    - OrderPlacedイベントを記録
    """
```

#### コマンドメソッド

```python
def transition_to(self, new_status: OrderStatus) -> None:
    """
    ステータスを遷移させる。
    不正な遷移の場合は InvalidStatusTransitionError を送出する。
    """

def cancel(self, reason: str) -> None:
    """
    注文をキャンセルする。
    キャンセル不可の状態（SHIPPED, DELIVERED）の場合は
    OrderCannotBeCancelledError を送出する。
    キャンセル成功時に OrderCancelled イベントを記録する。
    """
```

#### 不変条件（Invariants）
- 注文明細は1件以上必須
- 合計金額は0以上
- ステータス遷移は定義された遷移のみ許可
- キャンセルは CONFIRMED / PAID / PREPARING のみ可能

---

### 集約内エンティティ: OrderItem

```
OrderItem
├── id: OrderItemId
├── product_id: ProductId          ※他集約へのIDによる参照
├── product_name: str              ※注文時点のスナップショット
├── unit_price: Money              ※注文時点のスナップショット
├── quantity: Quantity
└── subtotal: Money                ※unit_price × quantity
```

#### 設計判断
- `product_name` と `unit_price` はスナップショットとして保持する。商品マスタが後から変更されても、注文時点の情報が維持される。
- OrderItem は独自のリポジトリを持たない。Order 集約経由でのみ永続化・取得する。

---

## 商品集約（Product Aggregate）

### 集約ルート: Product

```
Product (集約ルート)
├── id: ProductId
├── name: ProductName
├── sku: SKU
├── price: Price
├── category: str
├── description: Optional[str]
└── deleted_at: Optional[datetime]
```

#### ファクトリメソッド

```python
@staticmethod
def create(
    name: ProductName,
    sku: SKU,
    price: Price,
    category: str,
    description: Optional[str] = None,
) -> "Product":
    """
    商品を生成する。
    - ProductIdを採番
    - 各値オブジェクトのバリデーションはコンストラクタで実施
    """
```

#### コマンドメソッド

```python
def update(
    self,
    name: ProductName,
    price: Price,
    category: str,
    description: Optional[str],
) -> None:
    """商品情報を更新する。"""

def delete(self) -> None:
    """
    論理削除する。deleted_at に現在日時を設定する。
    """
```

#### 不変条件
- SKUは空でないこと
- 価格は0以上
- 論理削除済みの商品は更新不可

---

## 在庫集約（Stock Aggregate）

### 集約ルート: Stock

在庫の引当と解放を管理する。楽観的ロック（version）で同時更新の競合を防止する。

```
Stock (集約ルート)
├── id: StockId
├── product_id: ProductId          ※他集約へのIDによる参照
├── quantity: StockQuantity        ※総在庫数
├── allocated_quantity: StockQuantity  ※引当済み数量
├── low_stock_threshold: int
└── version: int                   ※楽観的ロック用
```

#### ファクトリメソッド

```python
@staticmethod
def initialize(product_id: ProductId, quantity: StockQuantity) -> "Stock":
    """
    初期在庫を生成する。
    - StockIdを採番
    - allocated_quantity は 0
    - version は 1
    """
```

#### コマンドメソッド

```python
def allocate(self, quantity: Quantity) -> None:
    """
    在庫を引当てる。
    引当可能数（quantity - allocated_quantity）が不足している場合は
    InsufficientStockError を送出する。
    引当成功時に StockAllocated イベントを記録する。
    引当後に在庫少閾値を下回った場合は LowStockDetected イベントも記録する。
    """

def release(self, quantity: Quantity) -> None:
    """
    引当済み在庫を解放する（キャンセル時）。
    StockReleased イベントを記録する。
    """

def add(self, quantity: Quantity) -> None:
    """
    在庫を追加する（入荷処理）。
    数量が0以下の場合は InvalidQuantityError を送出する。
    """
```

#### 算出プロパティ

```python
@property
def available_quantity(self) -> StockQuantity:
    """引当可能数 = quantity - allocated_quantity"""

@property
def is_low_stock(self) -> bool:
    """available_quantity <= low_stock_threshold"""
```

#### 不変条件
- quantity >= 0
- allocated_quantity >= 0
- allocated_quantity <= quantity

#### 設計判断: 在庫を注文集約と分離する理由
- 在庫の更新頻度は注文の参照頻度と異なる
- 楽観的ロックの粒度を在庫単位にすることで、同時注文時のロック競合範囲を最小化する
- 注文集約からは `product_id` による間接参照のみ行い、在庫の操作はApplication層で協調する

---

## 顧客集約（Customer Aggregate）

### 集約ルート: Customer

```
Customer (集約ルート)
├── id: CustomerId
├── name: CustomerName
├── email: EmailAddress
├── member_rank: MemberRank
├── shipping_addresses: List[ShippingAddress]  ※集約内エンティティ
└── created_at: datetime
```

#### ファクトリメソッド

```python
@staticmethod
def create(name: CustomerName, email: EmailAddress) -> "Customer":
    """
    顧客を生成する。
    - CustomerIdを採番
    - MemberRank は BRONZE で初期化
    """
```

#### コマンドメソッド

```python
def update(self, name: CustomerName, email: EmailAddress) -> None:
    """顧客情報を更新する。"""

def add_shipping_address(self, address: ShippingAddress) -> None:
    """
    配送先住所を追加する。
    最大5件まで。超過時は MaxAddressLimitExceededError。
    is_default=True の場合、既存のデフォルトを解除する。
    """

def get_shipping_address(self, address_id: str) -> ShippingAddress:
    """
    指定IDの配送先住所を取得する。
    存在しない場合は ShippingAddressNotFoundError。
    """
```

#### 不変条件
- 配送先住所は最大5件
- デフォルト住所は常に1件のみ

---

### 集約内エンティティ: ShippingAddress

```
ShippingAddress
├── id: str
├── label: str
├── address: Address               ※値オブジェクト
└── is_default: bool
```

---

## 値オブジェクト一覧

### ID系

| 値オブジェクト | 内部型 | 生成方法 | バリデーション |
|-------------|-------|---------|-------------|
| OrderId | str | UUID v4 | 空でないこと |
| OrderItemId | str | UUID v4 | 空でないこと |
| ProductId | str | UUID v4 | 空でないこと |
| StockId | str | UUID v4 | 空でないこと |
| CustomerId | str | UUID v4 | 空でないこと |
| CouponId | str | UUID v4 | 空でないこと |

### 金額・数量系

#### Money
```python
class Money:
    """
    金額を表す値オブジェクト。円単位の整数で保持する。
    浮動小数点の誤差を避けるため、すべて整数演算で行う。
    """
    amount: int  # 円単位

    def add(self, other: "Money") -> "Money": ...
    def subtract(self, other: "Money") -> "Money": ...
    def multiply(self, quantity: int) -> "Money": ...
    def apply_rate(self, rate: Decimal) -> "Money":
        """割合を適用する。端数は切り捨て。"""

    # 不変条件: amount >= 0
```

#### Price
```python
class Price:
    """
    商品単価を表す値オブジェクト。
    Moneyとは異なり、商品の価格としてのバリデーションを持つ。
    """
    value: int  # 円単位

    # 不変条件: value >= 0
```

#### Quantity
```python
class Quantity:
    """注文数量を表す値オブジェクト。"""
    value: int

    # 不変条件: value > 0
```

#### StockQuantity
```python
class StockQuantity:
    """在庫数量を表す値オブジェクト。0を許容する。"""
    value: int

    # 不変条件: value >= 0
```

### ステータス系

#### OrderStatus
```python
class OrderStatus(Enum):
    """
    注文ステータスを表す値オブジェクト。
    遷移可能なステータスのマッピングを保持する。
    """
    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    PREPARING = "PREPARING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

    def can_transition_to(self, new_status: "OrderStatus") -> bool:
        """遷移可能かどうかを判定する。"""
        allowed = {
            OrderStatus.CONFIRMED: [OrderStatus.PAID, OrderStatus.CANCELLED],
            OrderStatus.PAID: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [],
            OrderStatus.CANCELLED: [],
        }
        return new_status in allowed[self]

    @property
    def is_cancellable(self) -> bool:
        return self in (
            OrderStatus.CONFIRMED,
            OrderStatus.PAID,
            OrderStatus.PREPARING,
        )
```

#### MemberRank
```python
class MemberRank(Enum):
    """会員ランクを表す値オブジェクト。"""
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"

    @property
    def discount_rate(self) -> Decimal:
        rates = {
            MemberRank.BRONZE: Decimal("0.03"),
            MemberRank.SILVER: Decimal("0.05"),
            MemberRank.GOLD: Decimal("0.10"),
        }
        return rates[self]
```

### 文字列系

#### ProductName
```python
class ProductName:
    """商品名。1文字以上200文字以下。"""
    value: str
```

#### SKU
```python
class SKU:
    """在庫管理単位コード。英数字とハイフンのみ、1〜50文字。"""
    value: str
    # パターン: ^[A-Za-z0-9\-]+$
```

#### CustomerName
```python
class CustomerName:
    """顧客名。1文字以上100文字以下。"""
    value: str
```

#### EmailAddress
```python
class EmailAddress:
    """メールアドレス。RFC準拠のフォーマット検証。"""
    value: str
```

#### CouponCode
```python
class CouponCode:
    """クーポンコード。英数字のみ、1〜50文字。"""
    value: str
```

#### OrderNumber
```python
class OrderNumber:
    """注文番号。表示用。形式: ord-YYYYMMDD-NNN"""
    value: str
```

### 住所

#### Address
```python
class Address:
    """
    住所を表す値オブジェクト。
    DBでは4カラムに展開して永続化する。
    """
    postal_code: str   # 形式: NNN-NNNN
    prefecture: str    # 都道府県
    city: str          # 市区町村
    street: str        # 番地以降
```

### 割引系

#### DiscountType
```python
class DiscountType(Enum):
    """クーポンの割引種別。"""
    FIXED = "FIXED"            # 固定額割引
    PERCENTAGE = "PERCENTAGE"  # 割合割引
```

---

## ドメインサービス

### OrderDomainService

複数の集約にまたがるビジネスロジックをドメインサービスとして実装する。

```python
class OrderDomainService:
    """注文に関するドメインサービス。"""

    def create_order(
        self,
        customer: Customer,
        shipping_address: ShippingAddress,
        products_with_quantities: List[Tuple[Product, Quantity]],
        stocks: List[Stock],
        coupon: Optional[Coupon],
    ) -> Order:
        """
        注文を作成する。

        処理:
        1. 各商品の在庫を引当てる（Stock.allocate）
        2. 割引を計算する（DiscountPolicy.calculate）
        3. 注文を生成する（Order.create）

        複数集約の協調が必要なため、ドメインサービスとして実装する。
        トランザクション制御はApplication層の責務。
        """
```

### DiscountPolicy

```python
class DiscountPolicy:
    """
    割引計算のドメインサービス。
    割引ルールを定義された優先順位で適用する。
    """

    def calculate(
        self,
        items: List[Tuple[Product, Quantity]],
        member_rank: MemberRank,
        coupon: Optional[Coupon],
    ) -> Money:
        """
        割引額を算出する。

        適用順序:
        1. 会員ランク割引 — 小計に対してランクに応じた割合を適用
        2. 数量割引 — 同一商品10個以上で5%OFF（商品単位）
        3. クーポン割引 — 固定額 or 割合を最終合計に適用

        各割引は前の割引適用後の金額に対して計算する。
        """
```

#### 割引計算の詳細

```
例: ゴールド会員、商品A(1000円)×12個、クーポン500円引き

1. 小計: 1000 × 12 = 12,000円

2. 会員ランク割引（ゴールド10%）:
   12,000 × 0.10 = 1,200円引き → 10,800円

3. 数量割引（商品A 12個 ≥ 10個 → 5%OFF）:
   10,800 × 0.05 = 540円引き → 10,260円

4. クーポン割引（500円引き）:
   10,260 - 500 = 9,760円

割引合計: 12,000 - 9,760 = 2,240円
```

### TaxCalculator

```python
class TaxCalculator:
    """税額計算のドメインサービス。"""

    TAX_RATE = Decimal("0.10")  # 消費税率10%

    def calculate(self, amount: Money) -> Money:
        """
        税額を算出する。端数は切り捨て。
        """
```

---

## ドメインイベント

### イベント一覧

| イベント名 | 発生元集約 | 発生タイミング | ペイロード |
|-----------|----------|-------------|----------|
| OrderPlaced | Order | 注文作成時 | order_id, customer_id, total_amount, ordered_at |
| OrderCancelled | Order | 注文キャンセル時 | order_id, cancel_reason, cancelled_at |
| OrderShipped | Order | ステータスがSHIPPEDに遷移時 | order_id, shipped_at |
| StockAllocated | Stock | 在庫引当時 | product_id, allocated_quantity |
| StockReleased | Stock | 在庫解放時 | product_id, released_quantity |
| LowStockDetected | Stock | 在庫が閾値以下になった時 | product_id, available_quantity, threshold |

### イベントの基底クラス

```python
class DomainEvent:
    """ドメインイベントの基底クラス。"""
    event_id: str          # UUID
    event_type: str        # イベント種別
    aggregate_type: str    # 集約種別
    aggregate_id: str      # 集約ID
    occurred_at: datetime  # 発生日時
    payload: dict          # イベントデータ
```

### イベントの管理方針
- 各集約ルートは `_domain_events: List[DomainEvent]` を内部に保持する
- コマンドメソッド実行時にイベントをリストに追加する
- Application層がリポジトリ経由で永続化する際に、イベントをOutboxテーブル（`domain_events`）に保存する
- 本プロジェクトではイベント発行はOutbox保存までとし、非同期コンシューマは実装しない

---

## ドメイン例外

| 例外クラス | 発生元 | 発生条件 |
|-----------|-------|---------|
| InsufficientStockError | Stock.allocate | 引当可能数 < 要求数量 |
| InvalidStatusTransitionError | Order.transition_to | 許可されないステータス遷移 |
| OrderCannotBeCancelledError | Order.cancel | SHIPPED/DELIVEREDからのキャンセル |
| InvalidQuantityError | Stock.add | 数量が0以下 |
| MaxAddressLimitExceededError | Customer.add_shipping_address | 配送先住所が5件を超過 |
| ShippingAddressNotFoundError | Customer.get_shipping_address | 指定IDの住所が存在しない |
| InvalidCouponError | DiscountPolicy | クーポンが無効または期限切れ |
| DuplicateSKUError | Application層 | SKUが重複 |
| DuplicateEmailError | Application層 | メールアドレスが重複 |
| ProductInUseError | Application層 | 未完了注文に含まれる商品の削除 |
| OptimisticLockError | Infrastructure層 | 楽観的ロックの競合 |

---

## リポジトリインターフェース

ドメイン層にインターフェース（抽象クラス）を定義し、Infrastructure層で実装する。

### OrderRepository

```python
class OrderRepository(ABC):
    @abstractmethod
    def find_by_id(self, order_id: OrderId) -> Optional[Order]: ...

    @abstractmethod
    def find_by_customer_id(
        self, customer_id: CustomerId,
        status: Optional[OrderStatus] = None,
        page: int = 1, per_page: int = 20,
    ) -> Tuple[List[Order], int]: ...

    @abstractmethod
    def exists_active_order_with_product(self, product_id: ProductId) -> bool: ...

    @abstractmethod
    def save(self, order: Order) -> None: ...
```

### ProductRepository

```python
class ProductRepository(ABC):
    @abstractmethod
    def find_by_id(self, product_id: ProductId) -> Optional[Product]: ...

    @abstractmethod
    def find_by_ids(self, product_ids: List[ProductId]) -> List[Product]: ...

    @abstractmethod
    def find_by_sku(self, sku: SKU) -> Optional[Product]: ...

    @abstractmethod
    def find_all(
        self, category: Optional[str] = None,
        page: int = 1, per_page: int = 20,
    ) -> Tuple[List[Product], int]: ...

    @abstractmethod
    def save(self, product: Product) -> None: ...
```

### StockRepository

```python
class StockRepository(ABC):
    @abstractmethod
    def find_by_product_id(self, product_id: ProductId) -> Optional[Stock]: ...

    @abstractmethod
    def save(self, stock: Stock) -> None:
        """楽観的ロックによる競合検出を含む。"""
        ...
```

### CustomerRepository

```python
class CustomerRepository(ABC):
    @abstractmethod
    def find_by_id(self, customer_id: CustomerId) -> Optional[Customer]: ...

    @abstractmethod
    def find_by_email(self, email: EmailAddress) -> Optional[Customer]: ...

    @abstractmethod
    def save(self, customer: Customer) -> None: ...
```

### CouponRepository

```python
class CouponRepository(ABC):
    @abstractmethod
    def find_by_code(self, code: CouponCode) -> Optional[Coupon]: ...

    @abstractmethod
    def save(self, coupon: Coupon) -> None: ...
```

---

## 集約間の参照ルール

集約間は必ずIDによる間接参照とする。オブジェクト参照（直接の関連）は持たない。

```
Order.customer_id: CustomerId     ← Customer集約へのID参照
OrderItem.product_id: ProductId   ← Product集約へのID参照
Stock.product_id: ProductId       ← Product集約へのID参照
```

**理由:**
- 集約の独立性を保つ（トランザクション境界を明確にする）
- 集約単位での永続化・取得を可能にする
- 不要な関連データの読み込みを防ぐ

---

## レイヤー間の依存関係

```
Presentation層  →  Application層  →  Domain層  ←  Infrastructure層
(FastAPI Router)   (UseCase)        (Entity,     (SQLAlchemy,
                                    ValueObject,  Repository実装)
                                    DomainService,
                                    Repository IF)
```

- Domain層はどの層にも依存しない（外部ライブラリ不使用）
- Infrastructure層はDomain層のリポジトリインターフェースに依存する（依存性逆転の原則）
- Application層はDomain層のオブジェクトとリポジトリインターフェースに依存する
- Presentation層はApplication層のユースケースに依存する
