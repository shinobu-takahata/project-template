# 設計書: 注文エンドポイント実装

## 実装アプローチ

### 全体方針
Order境界づけられたコンテキストを新規作成し、既存のCustomer、Product、Stock境界コンテキストと連携する形で注文管理機能を実装する。DDDレイヤードアーキテクチャに従い、以下の4層構造で実装する。

**レイヤー構成**
- **Domain層**: Order集約（エンティティ、値オブジェクト）、ドメインサービス、割引ポリシー、リポジトリインターフェース
- **Application層**: 4つのユースケース、DTO
- **Infrastructure層**: SQLAlchemyモデル（2.0スタイル）、リポジトリ実装、イベントバス
- **Presentation層**: Pydanticスキーマ、FastAPIエンドポイント

**トランザクション戦略**
- 注文作成と在庫引当は同一トランザクション内で実行
- 注文キャンセルと在庫解放は同一トランザクション内で実行
- Application層のUseCaseでトランザクション境界を管理（commit/rollback）

**既存コンポーネントとの連携**
- CustomerRepository経由で顧客情報と配送先住所を取得
- ProductRepository経由で商品情報を取得（新規メソッド `find_by_ids` を追加）
- StockRepository経由で在庫情報を取得・更新
- Stock エンティティに `allocate`/`release` メソッドを追加

---

## 新規作成コンポーネント詳細設計

### Domain層

#### 1. Order エンティティ（集約ルート）
**ファイルパス**: `backend/app/domain/order/entities/order.py`

```python
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.order.entities.order_item import OrderItem
from app.domain.order.value_objects.order_id import OrderId
from app.domain.order.value_objects.order_status import OrderStatus
from app.domain.order.value_objects.money import Money
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.order.value_objects.shipping_address import ShippingAddress


@dataclass
class Order:
    """注文エンティティ（集約ルート）"""

    id: OrderId
    customer_id: CustomerId
    status: OrderStatus
    items: list[OrderItem]
    subtotal: Money
    discount_amount: Money
    tax_amount: Money
    shipping_fee: Money
    total_amount: Money
    shipping_address: ShippingAddress
    cancel_reason: str | None = None
    ordered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def create(
        customer_id: CustomerId,
        items: list[OrderItem],
        shipping_address: ShippingAddress,
        subtotal: Money,
        discount_amount: Money,
        tax_amount: Money,
        shipping_fee: Money,
        total_amount: Money,
    ) -> "Order":
        """注文を生成する（ファクトリメソッド）"""
        now = datetime.now(UTC)
        return Order(
            id=OrderId.generate(),
            customer_id=customer_id,
            status=OrderStatus.CONFIRMED,
            items=items,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            shipping_fee=shipping_fee,
            total_amount=total_amount,
            shipping_address=shipping_address,
            cancel_reason=None,
            ordered_at=now,
            updated_at=now,
        )

    def transition_to(self, new_status: OrderStatus) -> None:
        """ステータスを遷移させる"""
        if not self.status.can_transition_to(new_status):
            raise ValueError(
                f"Invalid status transition from {self.status.value} to {new_status.value}"
            )

        self.status = new_status
        self.updated_at = datetime.now(UTC)

    def cancel(self, reason: str) -> None:
        """注文をキャンセルする"""
        if not self.status.is_cancellable():
            raise ValueError(
                f"Order in {self.status.value} status cannot be cancelled"
            )

        self.status = OrderStatus.CANCELLED
        self.cancel_reason = reason
        self.updated_at = datetime.now(UTC)

    @property
    def is_cancelled(self) -> bool:
        """キャンセル済みかどうか"""
        return self.status == OrderStatus.CANCELLED
```

#### 2. OrderItem エンティティ
**ファイルパス**: `backend/app/domain/order/entities/order_item.py`

```python
from dataclasses import dataclass

from app.domain.product.value_objects.product_id import ProductId
from app.domain.order.value_objects.money import Money


@dataclass
class OrderItem:
    """注文明細エンティティ"""

    product_id: ProductId
    product_name: str
    unit_price: Money
    quantity: int

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

    @property
    def subtotal(self) -> Money:
        """小計を計算する"""
        return Money(self.unit_price.value * self.quantity)
```

#### 3. OrderStatus 値オブジェクト
**ファイルパス**: `backend/app/domain/order/value_objects/order_status.py`

```python
from enum import Enum


class OrderStatus(str, Enum):
    """注文ステータス値オブジェクト"""

    CONFIRMED = "CONFIRMED"  # 注文確定
    PAID = "PAID"            # 支払い完了
    PREPARING = "PREPARING"  # 準備中
    SHIPPED = "SHIPPED"      # 出荷済み
    DELIVERED = "DELIVERED"  # 配達完了
    CANCELLED = "CANCELLED"  # キャンセル

    # ステータス遷移マップ
    _TRANSITIONS = {
        CONFIRMED: [PAID],
        PAID: [PREPARING],
        PREPARING: [SHIPPED],
        SHIPPED: [DELIVERED],
        DELIVERED: [],
        CANCELLED: [],
    }

    # キャンセル可能ステータス
    _CANCELLABLE = {CONFIRMED, PAID, PREPARING}

    def can_transition_to(self, new_status: "OrderStatus") -> bool:
        """指定されたステータスへの遷移が可能か判定する"""
        return new_status in self._TRANSITIONS.get(self, [])

    def is_cancellable(self) -> bool:
        """キャンセル可能か判定する"""
        return self in self._CANCELLABLE
```

#### 4. Money 値オブジェクト
**ファイルパス**: `backend/app/domain/order/value_objects/money.py`

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    """金額値オブジェクト（円単位）"""

    value: int

    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Money must be non-negative")

    def add(self, other: "Money") -> "Money":
        """加算"""
        return Money(self.value + other.value)

    def subtract(self, other: "Money") -> "Money":
        """減算"""
        result = self.value - other.value
        if result < 0:
            raise ValueError("Subtraction result cannot be negative")
        return Money(result)

    def multiply(self, factor: int | float) -> "Money":
        """乗算"""
        return Money(int(self.value * factor))

    def calculate_tax(self, tax_rate: float = 0.1) -> "Money":
        """消費税を計算（デフォルト10%）"""
        return Money(int(self.value * tax_rate))
```

#### 5. OrderId 値オブジェクト
**ファイルパス**: `backend/app/domain/order/value_objects/order_id.py`

```python
from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class OrderId:
    """注文ID値オブジェクト"""

    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("OrderId cannot be empty")

    @staticmethod
    def generate() -> "OrderId":
        """新しいOrderIdを生成する"""
        return OrderId(str(uuid.uuid4()))
```

#### 6. ShippingAddress 値オブジェクト
**ファイルパス**: `backend/app/domain/order/value_objects/shipping_address.py`

```python
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ShippingAddress:
    """配送先住所値オブジェクト"""

    postal_code: str
    prefecture: str
    city: str
    street: str

    POSTAL_CODE_PATTERN = re.compile(r"^\d{3}-\d{4}$")

    def __post_init__(self):
        if not self.postal_code or not self.POSTAL_CODE_PATTERN.match(self.postal_code):
            raise ValueError(
                f"Postal code must be in NNN-NNNN format: {self.postal_code}"
            )

        if not self.prefecture or len(self.prefecture.strip()) == 0:
            raise ValueError("Prefecture cannot be empty")
        if not self.city or len(self.city.strip()) == 0:
            raise ValueError("City cannot be empty")
        if not self.street or len(self.street.strip()) == 0:
            raise ValueError("Street cannot be empty")
```

#### 7. DiscountPolicy（割引ポリシー）
**ファイルパス**: `backend/app/domain/order/services/discount_policy.py`

```python
from app.domain.customer.value_objects.member_rank import MemberRank
from app.domain.order.value_objects.money import Money


class DiscountPolicy:
    """割引ポリシー（ドメインサービス）"""

    # 会員ランク別割引率
    MEMBER_RANK_DISCOUNT = {
        MemberRank.BRONZE: 0.0,
        MemberRank.SILVER: 0.05,  # 5%
        MemberRank.GOLD: 0.10,    # 10%
    }

    # 数量割引（5個以上で10%割引）
    QUANTITY_DISCOUNT_THRESHOLD = 5
    QUANTITY_DISCOUNT_RATE = 0.10

    @staticmethod
    def apply_member_rank_discount(subtotal: Money, member_rank: MemberRank) -> Money:
        """会員ランク割引を適用"""
        discount_rate = DiscountPolicy.MEMBER_RANK_DISCOUNT.get(member_rank, 0.0)
        return subtotal.multiply(discount_rate)

    @staticmethod
    def apply_quantity_discount(unit_price: Money, quantity: int) -> Money:
        """数量割引を適用（商品単位）"""
        if quantity >= DiscountPolicy.QUANTITY_DISCOUNT_THRESHOLD:
            total = unit_price.multiply(quantity)
            return total.multiply(DiscountPolicy.QUANTITY_DISCOUNT_RATE)
        return Money(0)

    @staticmethod
    def apply_coupon_discount(total: Money, coupon_code: str | None) -> Money:
        """クーポン割引を適用（簡易実装）"""
        # 今回のスコープでは簡易的な検証のみ
        if coupon_code == "SPRING2026":
            return total.multiply(0.10)  # 10%割引
        return Money(0)
```

#### 8. OrderDomainService（ドメインサービス）
**ファイルパス**: `backend/app/domain/order/services/order_domain_service.py`

```python
from app.domain.order.entities.order import Order
from app.domain.order.entities.order_item import OrderItem
from app.domain.order.value_objects.money import Money
from app.domain.order.value_objects.shipping_address import ShippingAddress
from app.domain.order.services.discount_policy import DiscountPolicy
from app.domain.customer.entities.customer import Customer
from app.domain.product.entities.product import Product
from app.domain.customer.value_objects.customer_id import CustomerId


class OrderDomainService:
    """注文ドメインサービス"""

    SHIPPING_FEE = Money(500)  # 固定配送料
    TAX_RATE = 0.1  # 消費税率10%

    @staticmethod
    def create_order(
        customer: Customer,
        products: list[Product],
        quantities: dict[str, int],  # {product_id: quantity}
        shipping_address: ShippingAddress,
        coupon_code: str | None = None,
    ) -> Order:
        """注文を生成する"""
        # 注文明細を生成
        items: list[OrderItem] = []
        subtotal = Money(0)

        for product in products:
            quantity = quantities.get(product.id.value, 0)
            if quantity <= 0:
                continue

            item = OrderItem(
                product_id=product.id,
                product_name=product.name.value,
                unit_price=Money(product.price.value),
                quantity=quantity,
            )
            items.append(item)
            subtotal = subtotal.add(item.subtotal)

        # 割引計算
        # 1. 会員ランク割引（小計に適用）
        member_discount = DiscountPolicy.apply_member_rank_discount(
            subtotal, customer.member_rank
        )

        # 2. 数量割引（商品単位）
        quantity_discount = Money(0)
        for item in items:
            discount = DiscountPolicy.apply_quantity_discount(
                item.unit_price, item.quantity
            )
            quantity_discount = quantity_discount.add(discount)

        # 3. クーポン割引（最終合計に適用）
        subtotal_after_discount = subtotal.subtract(member_discount).subtract(
            quantity_discount
        )
        coupon_discount = DiscountPolicy.apply_coupon_discount(
            subtotal_after_discount, coupon_code
        )

        total_discount = member_discount.add(quantity_discount).add(coupon_discount)

        # 税込合計金額を計算
        subtotal_after_all_discount = subtotal.subtract(total_discount)
        tax_amount = subtotal_after_all_discount.calculate_tax(
            OrderDomainService.TAX_RATE
        )
        total_amount = (
            subtotal_after_all_discount.add(tax_amount).add(
                OrderDomainService.SHIPPING_FEE
            )
        )

        # 注文エンティティを生成
        return Order.create(
            customer_id=CustomerId(customer.id.value),
            items=items,
            shipping_address=shipping_address,
            subtotal=subtotal,
            discount_amount=total_discount,
            tax_amount=tax_amount,
            shipping_fee=OrderDomainService.SHIPPING_FEE,
            total_amount=total_amount,
        )
```

#### 9. OrderRepository インターフェース
**ファイルパス**: `backend/app/domain/order/repositories/order_repository.py`

```python
from abc import ABC, abstractmethod

from app.domain.order.entities.order import Order
from app.domain.order.value_objects.order_id import OrderId
from app.domain.customer.value_objects.customer_id import CustomerId


class IOrderRepository(ABC):
    """注文リポジトリインターフェース"""

    @abstractmethod
    def save(self, order: Order) -> None:
        """注文を保存する"""
        pass

    @abstractmethod
    def find_by_id(self, order_id: OrderId) -> Order | None:
        """注文IDで注文を取得する"""
        pass

    @abstractmethod
    def find_by_customer_id(
        self,
        customer_id: CustomerId,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Order], int]:
        """顧客IDで注文一覧を取得する"""
        pass

    @abstractmethod
    def exists_active_order_with_product(self, product_id: str) -> bool:
        """未完了注文に商品が含まれているか確認する"""
        pass
```

#### 10. 例外クラス
**ファイルパス**: `backend/app/domain/order/exceptions.py`

```python
class OrderDomainError(Exception):
    """注文ドメインエラー基底クラス"""
    pass


class InsufficientStockError(OrderDomainError):
    """在庫不足エラー"""
    pass


class InvalidStatusTransitionError(OrderDomainError):
    """不正なステータス遷移エラー"""
    pass


class OrderCannotBeCancelledError(OrderDomainError):
    """注文キャンセル不可エラー"""
    pass
```

---

### Application層

#### 1. CreateOrderUseCase
**ファイルパス**: `backend/app/application/order/usecases/create_order_usecase.py`

```python
from sqlalchemy.orm import Session

from app.application.order.dtos.order_dto import OrderDTO, CreateOrderInputDTO
from app.application.order.exceptions import (
    CustomerNotFoundError,
    ProductNotFoundError,
    InsufficientStockError,
    InvalidShippingAddressError,
)
from app.domain.customer.repositories.customer_repository import ICustomerRepository
from app.domain.product.repositories.product_repository import IProductRepository
from app.domain.stock.repositories.stock_repository import IStockRepository
from app.domain.order.repositories.order_repository import IOrderRepository
from app.domain.order.services.order_domain_service import OrderDomainService
from app.domain.order.value_objects.shipping_address import ShippingAddress
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.product.value_objects.product_id import ProductId


class CreateOrderUseCase:
    """注文作成ユースケース"""

    def __init__(
        self,
        customer_repository: ICustomerRepository,
        product_repository: IProductRepository,
        stock_repository: IStockRepository,
        order_repository: IOrderRepository,
        db: Session,
    ):
        self.customer_repository = customer_repository
        self.product_repository = product_repository
        self.stock_repository = stock_repository
        self.order_repository = order_repository
        self.db = db

    def execute(self, input_dto: CreateOrderInputDTO) -> OrderDTO:
        # 顧客取得
        customer = self.customer_repository.find_by_id(
            CustomerId(input_dto.customer_id)
        )
        if customer is None:
            raise CustomerNotFoundError(
                f"Customer with ID '{input_dto.customer_id}' not found"
            )

        # 配送先住所検証
        try:
            shipping_address_entity = customer.get_shipping_address(
                input_dto.shipping_address_id
            )
        except ValueError:
            raise InvalidShippingAddressError(
                f"Shipping address '{input_dto.shipping_address_id}' not found"
            )

        shipping_address = ShippingAddress(
            postal_code=shipping_address_entity.address.postal_code,
            prefecture=shipping_address_entity.address.prefecture,
            city=shipping_address_entity.address.city,
            street=shipping_address_entity.address.street,
        )

        # 商品情報取得
        product_ids = [ProductId(item.product_id) for item in input_dto.items]
        products = self.product_repository.find_by_ids(product_ids)

        if len(products) != len(product_ids):
            raise ProductNotFoundError("One or more products not found")

        # 在庫確認と引当
        quantities = {item.product_id: item.quantity for item in input_dto.items}
        for product in products:
            stock = self.stock_repository.find_by_product_id(product.id)
            if stock is None:
                raise InsufficientStockError(
                    f"Stock for product '{product.id.value}' not found"
                )

            quantity = quantities.get(product.id.value, 0)
            stock.allocate(quantity)  # 在庫引当（不足時は例外発生）

        # ドメインサービスで注文生成
        order = OrderDomainService.create_order(
            customer=customer,
            products=products,
            quantities=quantities,
            shipping_address=shipping_address,
            coupon_code=input_dto.coupon_code,
        )

        # 永続化
        try:
            self.order_repository.save(order)
            for product in products:
                stock = self.stock_repository.find_by_product_id(product.id)
                self.stock_repository.save(stock)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

        # DTOに変換して返却
        return OrderDTO.from_entity(order)
```

#### 2. GetOrderUseCase
**ファイルパス**: `backend/app/application/order/usecases/get_order_usecase.py`

```python
from app.application.order.dtos.order_dto import OrderDTO
from app.application.order.exceptions import OrderNotFoundError
from app.domain.order.repositories.order_repository import IOrderRepository
from app.domain.order.value_objects.order_id import OrderId


class GetOrderUseCase:
    """注文詳細取得ユースケース"""

    def __init__(self, order_repository: IOrderRepository):
        self.order_repository = order_repository

    def execute(self, order_id: str) -> OrderDTO:
        order = self.order_repository.find_by_id(OrderId(order_id))
        if order is None:
            raise OrderNotFoundError(f"Order with ID '{order_id}' not found")

        return OrderDTO.from_entity(order)
```

#### 3. UpdateOrderStatusUseCase
**ファイルパス**: `backend/app/application/order/usecases/update_order_status_usecase.py`

```python
from sqlalchemy.orm import Session

from app.application.order.dtos.order_dto import OrderStatusUpdateDTO
from app.application.order.exceptions import (
    OrderNotFoundError,
    InvalidStatusTransitionError,
)
from app.domain.order.repositories.order_repository import IOrderRepository
from app.domain.order.value_objects.order_id import OrderId
from app.domain.order.value_objects.order_status import OrderStatus


class UpdateOrderStatusUseCase:
    """注文ステータス更新ユースケース"""

    def __init__(self, order_repository: IOrderRepository, db: Session):
        self.order_repository = order_repository
        self.db = db

    def execute(self, order_id: str, new_status: str) -> OrderStatusUpdateDTO:
        order = self.order_repository.find_by_id(OrderId(order_id))
        if order is None:
            raise OrderNotFoundError(f"Order with ID '{order_id}' not found")

        previous_status = order.status.value

        try:
            order.transition_to(OrderStatus(new_status))
        except ValueError as e:
            raise InvalidStatusTransitionError(str(e))

        try:
            self.order_repository.save(order)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

        return OrderStatusUpdateDTO(
            order_id=order.id.value,
            previous_status=previous_status,
            current_status=order.status.value,
            updated_at=order.updated_at,
        )
```

#### 4. CancelOrderUseCase
**ファイルパス**: `backend/app/application/order/usecases/cancel_order_usecase.py`

```python
from sqlalchemy.orm import Session

from app.application.order.dtos.order_dto import OrderCancelDTO
from app.application.order.exceptions import (
    OrderNotFoundError,
    OrderCannotBeCancelledError,
)
from app.domain.order.repositories.order_repository import IOrderRepository
from app.domain.stock.repositories.stock_repository import IStockRepository
from app.domain.order.value_objects.order_id import OrderId


class CancelOrderUseCase:
    """注文キャンセルユースケース"""

    def __init__(
        self,
        order_repository: IOrderRepository,
        stock_repository: IStockRepository,
        db: Session,
    ):
        self.order_repository = order_repository
        self.stock_repository = stock_repository
        self.db = db

    def execute(self, order_id: str, reason: str) -> OrderCancelDTO:
        order = self.order_repository.find_by_id(OrderId(order_id))
        if order is None:
            raise OrderNotFoundError(f"Order with ID '{order_id}' not found")

        try:
            order.cancel(reason)
        except ValueError as e:
            raise OrderCannotBeCancelledError(str(e))

        # 在庫を戻す
        for item in order.items:
            stock = self.stock_repository.find_by_product_id(item.product_id)
            if stock is not None:
                stock.release(item.quantity)

        try:
            self.order_repository.save(order)
            for item in order.items:
                stock = self.stock_repository.find_by_product_id(item.product_id)
                if stock is not None:
                    self.stock_repository.save(stock)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

        return OrderCancelDTO(
            order_id=order.id.value,
            status=order.status.value,
            cancel_reason=order.cancel_reason,
            cancelled_at=order.updated_at,
        )
```

#### 5. DTO定義
**ファイルパス**: `backend/app/application/order/dtos/order_dto.py`

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass
class OrderItemInputDTO:
    """注文明細入力DTO"""
    product_id: str
    quantity: int


@dataclass
class CreateOrderInputDTO:
    """注文作成入力DTO"""
    customer_id: str
    shipping_address_id: str
    items: list[OrderItemInputDTO]
    coupon_code: str | None = None


@dataclass
class OrderItemDTO:
    """注文明細DTO"""
    product_id: str
    product_name: str
    unit_price: int
    quantity: int
    subtotal: int


@dataclass
class ShippingAddressDTO:
    """配送先住所DTO"""
    postal_code: str
    prefecture: str
    city: str
    street: str


@dataclass
class OrderDTO:
    """注文DTO"""
    order_id: str
    status: str
    customer_id: str
    items: list[OrderItemDTO]
    subtotal: int
    discount_amount: int
    tax_amount: int
    shipping_fee: int
    total_amount: int
    shipping_address: ShippingAddressDTO
    ordered_at: datetime

    @staticmethod
    def from_entity(order) -> "OrderDTO":
        """OrderエンティティからDTOに変換"""
        return OrderDTO(
            order_id=order.id.value,
            status=order.status.value,
            customer_id=order.customer_id.value,
            items=[
                OrderItemDTO(
                    product_id=item.product_id.value,
                    product_name=item.product_name,
                    unit_price=item.unit_price.value,
                    quantity=item.quantity,
                    subtotal=item.subtotal.value,
                )
                for item in order.items
            ],
            subtotal=order.subtotal.value,
            discount_amount=order.discount_amount.value,
            tax_amount=order.tax_amount.value,
            shipping_fee=order.shipping_fee.value,
            total_amount=order.total_amount.value,
            shipping_address=ShippingAddressDTO(
                postal_code=order.shipping_address.postal_code,
                prefecture=order.shipping_address.prefecture,
                city=order.shipping_address.city,
                street=order.shipping_address.street,
            ),
            ordered_at=order.ordered_at,
        )


@dataclass
class OrderStatusUpdateDTO:
    """注文ステータス更新DTO"""
    order_id: str
    previous_status: str
    current_status: str
    updated_at: datetime


@dataclass
class OrderCancelDTO:
    """注文キャンセルDTO"""
    order_id: str
    status: str
    cancel_reason: str | None
    cancelled_at: datetime
```

#### 6. 例外クラス
**ファイルパス**: `backend/app/application/order/exceptions.py`

```python
class OrderApplicationError(Exception):
    """注文アプリケーションエラー基底クラス"""
    pass


class CustomerNotFoundError(OrderApplicationError):
    """顧客未検出エラー"""
    pass


class ProductNotFoundError(OrderApplicationError):
    """商品未検出エラー"""
    pass


class InsufficientStockError(OrderApplicationError):
    """在庫不足エラー"""
    pass


class InvalidCouponError(OrderApplicationError):
    """無効なクーポンエラー"""
    pass


class InvalidShippingAddressError(OrderApplicationError):
    """無効な配送先住所エラー"""
    pass


class OrderNotFoundError(OrderApplicationError):
    """注文未検出エラー"""
    pass


class InvalidStatusTransitionError(OrderApplicationError):
    """不正なステータス遷移エラー"""
    pass


class OrderCannotBeCancelledError(OrderApplicationError):
    """注文キャンセル不可エラー"""
    pass
```

---

### Infrastructure層

#### 1. SQLAlchemyモデル（2.0スタイル）
**ファイルパス**: `backend/app/infrastructure/database/models.py`（既存ファイルに追加）

```python
# 以下を既存のmodels.pyに追加

class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(String(20), default="CONFIRMED")
    subtotal: Mapped[int] = mapped_column(Integer)
    discount_amount: Mapped[int] = mapped_column(Integer, default=0)
    tax_amount: Mapped[int] = mapped_column(Integer)
    shipping_fee: Mapped[int] = mapped_column(Integer)
    total_amount: Mapped[int] = mapped_column(Integer)
    shipping_postal_code: Mapped[str] = mapped_column(String(10))
    shipping_prefecture: Mapped[str] = mapped_column(String(10))
    shipping_city: Mapped[str] = mapped_column(String(100))
    shipping_street: Mapped[str] = mapped_column(String(200))
    cancel_reason: Mapped[str | None] = mapped_column(Text, default=None)
    ordered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    items: Mapped[list["OrderItemModel"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('CONFIRMED', 'PAID', 'PREPARING', 'SHIPPED', 'DELIVERED', 'CANCELLED')",
            name="check_order_status",
        ),
        CheckConstraint("subtotal >= 0", name="check_subtotal_non_negative"),
        CheckConstraint("discount_amount >= 0", name="check_discount_non_negative"),
        CheckConstraint("tax_amount >= 0", name="check_tax_non_negative"),
        CheckConstraint("shipping_fee >= 0", name="check_shipping_fee_non_negative"),
        CheckConstraint("total_amount >= 0", name="check_total_non_negative"),
        Index("idx_orders_customer_id", "customer_id"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_ordered_at", "ordered_at"),
    )


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"))
    product_id: Mapped[str] = mapped_column(String(36))
    product_name: Mapped[str] = mapped_column(String(200))
    unit_price: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)

    order: Mapped["OrderModel"] = relationship(back_populates="items")

    __table_args__ = (
        CheckConstraint("unit_price >= 0", name="check_unit_price_non_negative"),
        CheckConstraint("quantity > 0", name="check_quantity_positive"),
        Index("idx_order_items_order_id", "order_id"),
        Index("idx_order_items_product_id", "product_id"),
    )
```

#### 2. OrderRepository実装
**ファイルパス**: `backend/app/infrastructure/repositories/order_repository.py`（既存スタブを置換）

```python
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.domain.order.entities.order import Order
from app.domain.order.entities.order_item import OrderItem
from app.domain.order.repositories.order_repository import IOrderRepository
from app.domain.order.value_objects.order_id import OrderId
from app.domain.order.value_objects.order_status import OrderStatus
from app.domain.order.value_objects.money import Money
from app.domain.order.value_objects.shipping_address import ShippingAddress
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.product.value_objects.product_id import ProductId
from app.infrastructure.database.models import OrderModel, OrderItemModel


class OrderRepository(IOrderRepository):
    """注文リポジトリ実装"""

    def __init__(self, db: Session):
        self.db = db

    def save(self, order: Order) -> None:
        exists = self.db.scalar(
            select(OrderModel.id).where(OrderModel.id == order.id.value)
        )

        if exists is None:
            # 新規作成
            model = OrderModel(
                id=order.id.value,
                customer_id=order.customer_id.value,
                status=order.status.value,
                subtotal=order.subtotal.value,
                discount_amount=order.discount_amount.value,
                tax_amount=order.tax_amount.value,
                shipping_fee=order.shipping_fee.value,
                total_amount=order.total_amount.value,
                shipping_postal_code=order.shipping_address.postal_code,
                shipping_prefecture=order.shipping_address.prefecture,
                shipping_city=order.shipping_address.city,
                shipping_street=order.shipping_address.street,
                cancel_reason=order.cancel_reason,
                ordered_at=order.ordered_at,
                updated_at=order.updated_at,
            )
            self.db.add(model)
            self.db.flush()

            # 注文明細を追加
            for item in order.items:
                item_model = OrderItemModel(
                    order_id=order.id.value,
                    product_id=item.product_id.value,
                    product_name=item.product_name,
                    unit_price=item.unit_price.value,
                    quantity=item.quantity,
                )
                self.db.add(item_model)
        else:
            # 更新
            stmt = (
                update(OrderModel)
                .where(OrderModel.id == order.id.value)
                .values(
                    status=order.status.value,
                    cancel_reason=order.cancel_reason,
                    updated_at=order.updated_at,
                )
            )
            self.db.execute(stmt)

        self.db.flush()

    def find_by_id(self, order_id: OrderId) -> Order | None:
        stmt = select(OrderModel).where(OrderModel.id == order_id.value)
        model = self.db.scalars(stmt).first()

        if model is None:
            return None

        return self._to_entity(model)

    def find_by_customer_id(
        self,
        customer_id: CustomerId,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Order], int]:
        stmt = select(OrderModel).where(OrderModel.customer_id == customer_id.value)

        if status:
            stmt = stmt.where(OrderModel.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page).order_by(OrderModel.ordered_at.desc())
        models = self.db.scalars(stmt).all()

        orders = [self._to_entity(m) for m in models]
        return orders, total

    def exists_active_order_with_product(self, product_id: str) -> bool:
        stmt = (
            select(OrderItemModel)
            .join(OrderModel)
            .where(
                OrderItemModel.product_id == product_id,
                OrderModel.status.in_(["CONFIRMED", "PAID", "PREPARING", "SHIPPED"]),
            )
        )
        result = self.db.scalars(stmt).first()
        return result is not None

    def _to_entity(self, model: OrderModel) -> Order:
        items = [
            OrderItem(
                product_id=ProductId(item.product_id),
                product_name=item.product_name,
                unit_price=Money(item.unit_price),
                quantity=item.quantity,
            )
            for item in model.items
        ]

        return Order(
            id=OrderId(model.id),
            customer_id=CustomerId(model.customer_id),
            status=OrderStatus(model.status),
            items=items,
            subtotal=Money(model.subtotal),
            discount_amount=Money(model.discount_amount),
            tax_amount=Money(model.tax_amount),
            shipping_fee=Money(model.shipping_fee),
            total_amount=Money(model.total_amount),
            shipping_address=ShippingAddress(
                postal_code=model.shipping_postal_code,
                prefecture=model.shipping_prefecture,
                city=model.shipping_city,
                street=model.shipping_street,
            ),
            cancel_reason=model.cancel_reason,
            ordered_at=model.ordered_at,
            updated_at=model.updated_at,
        )
```

---

### Presentation層

#### 1. Pydanticスキーマ
**ファイルパス**: `backend/app/schemas/order.py`

```python
from datetime import datetime
from pydantic import BaseModel, Field


class OrderItemRequest(BaseModel):
    """注文明細リクエスト"""
    product_id: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)


class OrderCreateRequest(BaseModel):
    """注文作成リクエスト"""
    customer_id: str = Field(..., min_length=1)
    shipping_address_id: str = Field(..., min_length=1)
    items: list[OrderItemRequest] = Field(..., min_length=1)
    coupon_code: str | None = None


class OrderItemResponse(BaseModel):
    """注文明細レスポンス"""
    product_id: str
    product_name: str
    unit_price: int
    quantity: int
    subtotal: int


class ShippingAddressResponse(BaseModel):
    """配送先住所レスポンス"""
    postal_code: str
    prefecture: str
    city: str
    street: str


class OrderResponse(BaseModel):
    """注文レスポンス"""
    order_id: str
    status: str
    customer_id: str
    items: list[OrderItemResponse]
    subtotal: int
    discount_amount: int
    tax_amount: int
    shipping_fee: int
    total_amount: int
    shipping_address: ShippingAddressResponse
    ordered_at: datetime


class OrderStatusUpdateRequest(BaseModel):
    """注文ステータス更新リクエスト"""
    status: str = Field(
        ...,
        pattern="^(CONFIRMED|PAID|PREPARING|SHIPPED|DELIVERED)$"
    )


class OrderStatusUpdateResponse(BaseModel):
    """注文ステータス更新レスポンス"""
    order_id: str
    previous_status: str
    current_status: str
    updated_at: datetime


class OrderCancelRequest(BaseModel):
    """注文キャンセルリクエスト"""
    reason: str = Field(..., min_length=1, max_length=500)


class OrderCancelResponse(BaseModel):
    """注文キャンセルレスポンス"""
    order_id: str
    status: str
    cancel_reason: str | None
    cancelled_at: datetime


class OrderDataResponse(BaseModel):
    """注文データラッパー"""
    data: OrderResponse


class OrderStatusDataResponse(BaseModel):
    """注文ステータスデータラッパー"""
    data: OrderStatusUpdateResponse


class OrderCancelDataResponse(BaseModel):
    """注文キャンセルデータラッパー"""
    data: OrderCancelResponse
```

#### 2. FastAPIエンドポイント
**ファイルパス**: `backend/app/api/v1/endpoints/orders.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.application.order.dtos.order_dto import (
    CreateOrderInputDTO,
    OrderItemInputDTO,
)
from app.application.order.exceptions import (
    CustomerNotFoundError,
    ProductNotFoundError,
    InsufficientStockError,
    InvalidShippingAddressError,
    OrderNotFoundError,
    InvalidStatusTransitionError,
    OrderCannotBeCancelledError,
)
from app.application.order.usecases.create_order_usecase import CreateOrderUseCase
from app.application.order.usecases.get_order_usecase import GetOrderUseCase
from app.application.order.usecases.update_order_status_usecase import (
    UpdateOrderStatusUseCase,
)
from app.application.order.usecases.cancel_order_usecase import CancelOrderUseCase
from app.core.database import get_db
from app.infrastructure.repositories.customer_repository import CustomerRepository
from app.infrastructure.repositories.product_repository import ProductRepository
from app.infrastructure.repositories.stock_repository import StockRepository
from app.infrastructure.repositories.order_repository import OrderRepository
from app.schemas.order import (
    OrderCreateRequest,
    OrderDataResponse,
    OrderStatusUpdateRequest,
    OrderStatusDataResponse,
    OrderCancelRequest,
    OrderCancelDataResponse,
    OrderItemResponse,
    OrderResponse,
    ShippingAddressResponse,
    OrderStatusUpdateResponse,
    OrderCancelResponse,
)

router = APIRouter()


@router.post("/", response_model=OrderDataResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    request: OrderCreateRequest,
    db: Session = Depends(get_db),
):
    """注文作成"""
    customer_repository = CustomerRepository(db)
    product_repository = ProductRepository(db)
    stock_repository = StockRepository(db)
    order_repository = OrderRepository(db)

    usecase = CreateOrderUseCase(
        customer_repository,
        product_repository,
        stock_repository,
        order_repository,
        db,
    )

    input_dto = CreateOrderInputDTO(
        customer_id=request.customer_id,
        shipping_address_id=request.shipping_address_id,
        items=[
            OrderItemInputDTO(product_id=item.product_id, quantity=item.quantity)
            for item in request.items
        ],
        coupon_code=request.coupon_code,
    )

    try:
        order_dto = usecase.execute(input_dto)
        return OrderDataResponse(
            data=OrderResponse(
                order_id=order_dto.order_id,
                status=order_dto.status,
                customer_id=order_dto.customer_id,
                items=[
                    OrderItemResponse(**item.__dict__) for item in order_dto.items
                ],
                subtotal=order_dto.subtotal,
                discount_amount=order_dto.discount_amount,
                tax_amount=order_dto.tax_amount,
                shipping_fee=order_dto.shipping_fee,
                total_amount=order_dto.total_amount,
                shipping_address=ShippingAddressResponse(
                    **order_dto.shipping_address.__dict__
                ),
                ordered_at=order_dto.ordered_at,
            )
        )
    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientStockError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidShippingAddressError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{order_id}", response_model=OrderDataResponse)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
):
    """注文詳細取得"""
    order_repository = OrderRepository(db)
    usecase = GetOrderUseCase(order_repository)

    try:
        order_dto = usecase.execute(order_id)
        return OrderDataResponse(
            data=OrderResponse(
                order_id=order_dto.order_id,
                status=order_dto.status,
                customer_id=order_dto.customer_id,
                items=[
                    OrderItemResponse(**item.__dict__) for item in order_dto.items
                ],
                subtotal=order_dto.subtotal,
                discount_amount=order_dto.discount_amount,
                tax_amount=order_dto.tax_amount,
                shipping_fee=order_dto.shipping_fee,
                total_amount=order_dto.total_amount,
                shipping_address=ShippingAddressResponse(
                    **order_dto.shipping_address.__dict__
                ),
                ordered_at=order_dto.ordered_at,
            )
        )
    except OrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{order_id}/status", response_model=OrderStatusDataResponse)
def update_order_status(
    order_id: str,
    request: OrderStatusUpdateRequest,
    db: Session = Depends(get_db),
):
    """注文ステータス更新"""
    order_repository = OrderRepository(db)
    usecase = UpdateOrderStatusUseCase(order_repository, db)

    try:
        status_dto = usecase.execute(order_id, request.status)
        return OrderStatusDataResponse(
            data=OrderStatusUpdateResponse(**status_dto.__dict__)
        )
    except OrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{order_id}/cancel", response_model=OrderCancelDataResponse)
def cancel_order(
    order_id: str,
    request: OrderCancelRequest,
    db: Session = Depends(get_db),
):
    """注文キャンセル"""
    order_repository = OrderRepository(db)
    stock_repository = StockRepository(db)
    usecase = CancelOrderUseCase(order_repository, stock_repository, db)

    try:
        cancel_dto = usecase.execute(order_id, request.reason)
        return OrderCancelDataResponse(
            data=OrderCancelResponse(**cancel_dto.__dict__)
        )
    except OrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except OrderCannotBeCancelledError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
```

---

## 既存コンポーネントへの変更

### 1. Stock エンティティへの変更
**ファイルパス**: `backend/app/domain/stock/entities/stock.py`

**追加メソッド**:
```python
def allocate(self, quantity: int) -> None:
    """在庫を引き当てる"""
    if quantity <= 0:
        raise ValueError("Allocation quantity must be positive")

    new_quantity = self.quantity.value - quantity
    if new_quantity < 0:
        raise ValueError(
            f"Insufficient stock: requested {quantity}, available {self.quantity.value}"
        )

    from app.domain.stock.value_objects.stock_quantity import StockQuantity
    self.quantity = StockQuantity(new_quantity)
    from datetime import UTC, datetime
    self.updated_at = datetime.now(UTC)

def release(self, quantity: int) -> None:
    """在庫を戻す"""
    if quantity <= 0:
        raise ValueError("Release quantity must be positive")

    from app.domain.stock.value_objects.stock_quantity import StockQuantity
    new_quantity = self.quantity.value + quantity
    self.quantity = StockQuantity(new_quantity)
    from datetime import UTC, datetime
    self.updated_at = datetime.now(UTC)
```

### 2. ProductRepository への変更
**ファイルパス**: `backend/app/domain/product/repositories/product_repository.py`

**追加メソッド**（インターフェース）:
```python
@abstractmethod
def find_by_ids(self, product_ids: list[ProductId]) -> list[Product]:
    """複数の商品IDで商品を一括取得する"""
    pass
```

**ファイルパス**: `backend/app/infrastructure/repositories/product_repository.py`

**追加メソッド**（実装）:
```python
def find_by_ids(self, product_ids: list[ProductId]) -> list[Product]:
    stmt = select(ProductModel).where(
        ProductModel.id.in_([pid.value for pid in product_ids]),
        ProductModel.deleted_at.is_(None),
    )
    models = self.db.scalars(stmt).all()
    return [self._to_entity(m) for m in models]
```

### 3. OrderRepository（既存スタブ）の完全実装
**ファイルパス**: `backend/app/infrastructure/repositories/order_repository.py`

スタブ実装を上記「Infrastructure層 > OrderRepository実装」の内容に完全置換する。

---

## データ構造（テーブル定義）

### ordersテーブル
| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | VARCHAR(36) | PRIMARY KEY | 注文ID（UUID） |
| customer_id | VARCHAR(36) | NOT NULL | 顧客ID |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'CONFIRMED' | ステータス |
| subtotal | INTEGER | NOT NULL, >= 0 | 小計 |
| discount_amount | INTEGER | NOT NULL, DEFAULT 0, >= 0 | 割引額 |
| tax_amount | INTEGER | NOT NULL, >= 0 | 税額 |
| shipping_fee | INTEGER | NOT NULL, >= 0 | 配送料 |
| total_amount | INTEGER | NOT NULL, >= 0 | 合計金額 |
| shipping_postal_code | VARCHAR(10) | NOT NULL | 配送先郵便番号 |
| shipping_prefecture | VARCHAR(10) | NOT NULL | 配送先都道府県 |
| shipping_city | VARCHAR(100) | NOT NULL | 配送先市区町村 |
| shipping_street | VARCHAR(200) | NOT NULL | 配送先番地 |
| cancel_reason | TEXT | NULL | キャンセル理由 |
| ordered_at | TIMESTAMP WITH TIME ZONE | NOT NULL | 注文日時 |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL | 更新日時 |

**インデックス**:
- `idx_orders_customer_id` (customer_id)
- `idx_orders_status` (status)
- `idx_orders_ordered_at` (ordered_at)

**CHECK制約**:
- status IN ('CONFIRMED', 'PAID', 'PREPARING', 'SHIPPED', 'DELIVERED', 'CANCELLED')
- 金額系カラムは全て非負

### order_itemsテーブル
| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | 明細ID |
| order_id | VARCHAR(36) | NOT NULL, FOREIGN KEY | 注文ID |
| product_id | VARCHAR(36) | NOT NULL | 商品ID |
| product_name | VARCHAR(200) | NOT NULL | 商品名（スナップショット） |
| unit_price | INTEGER | NOT NULL, >= 0 | 単価 |
| quantity | INTEGER | NOT NULL, > 0 | 数量 |

**インデックス**:
- `idx_order_items_order_id` (order_id)
- `idx_order_items_product_id` (product_id)

**CHECK制約**:
- unit_price >= 0
- quantity > 0

---

## ディレクトリ構成（新規ファイル一覧）

```
backend/app/
├── domain/
│   └── order/                           # 新規ディレクトリ
│       ├── __init__.py
│       ├── entities/
│       │   ├── __init__.py
│       │   ├── order.py                 # Orderエンティティ
│       │   └── order_item.py            # OrderItemエンティティ
│       ├── value_objects/
│       │   ├── __init__.py
│       │   ├── order_id.py              # OrderId値オブジェクト
│       │   ├── order_status.py          # OrderStatus値オブジェクト
│       │   ├── money.py                 # Money値オブジェクト
│       │   └── shipping_address.py      # ShippingAddress値オブジェクト
│       ├── services/
│       │   ├── __init__.py
│       │   ├── order_domain_service.py  # OrderDomainService
│       │   └── discount_policy.py       # DiscountPolicy
│       ├── repositories/
│       │   ├── __init__.py
│       │   └── order_repository.py      # IOrderRepositoryインターフェース
│       └── exceptions.py                # ドメイン例外
├── application/
│   └── order/                           # 新規ディレクトリ
│       ├── __init__.py
│       ├── dtos/
│       │   ├── __init__.py
│       │   └── order_dto.py             # DTO定義
│       ├── usecases/
│       │   ├── __init__.py
│       │   ├── create_order_usecase.py  # 注文作成ユースケース
│       │   ├── get_order_usecase.py     # 注文詳細取得ユースケース
│       │   ├── update_order_status_usecase.py  # ステータス更新ユースケース
│       │   └── cancel_order_usecase.py  # キャンセルユースケース
│       └── exceptions.py                # アプリケーション例外
├── infrastructure/
│   ├── database/
│   │   └── models.py                    # 変更: OrderModel, OrderItemModel追加
│   └── repositories/
│       └── order_repository.py          # 変更: スタブから完全実装に置換
├── schemas/
│   └── order.py                         # 新規: Pydanticスキーマ
└── api/
    └── v1/
        └── endpoints/
            └── orders.py                # 新規: 注文エンドポイント
```

**既存ファイルの変更**:
- `backend/app/domain/stock/entities/stock.py` - allocate/releaseメソッド追加
- `backend/app/domain/product/repositories/product_repository.py` - find_by_idsメソッド追加（インターフェース）
- `backend/app/infrastructure/repositories/product_repository.py` - find_by_idsメソッド追加（実装）
- `backend/app/infrastructure/database/models.py` - OrderModel, OrderItemModel追加
- `backend/app/infrastructure/repositories/order_repository.py` - スタブから完全実装に置換
- `backend/app/api/v1/router.py` - 注文エンドポイントのルーティング追加

---

## 影響範囲の分析

### 既存コンポーネントへの影響

#### 1. Customer境界コンテキスト
**影響**: なし（参照のみ）
- CustomerRepositoryの既存メソッドを使用
- Customerエンティティの既存メソッド（get_shipping_address）を使用

#### 2. Product境界コンテキスト
**影響**: あり（軽微）
- **変更内容**: ProductRepositoryに `find_by_ids` メソッドを追加
- **理由**: 複数商品を一括取得するため
- **互換性**: 既存機能への影響なし（新規メソッド追加のみ）

#### 3. Stock境界コンテキスト
**影響**: あり（中程度）
- **変更内容**: Stockエンティティに `allocate` / `release` メソッドを追加
- **理由**: 在庫引当・解放のビジネスロジックをドメイン層に集約
- **互換性**: 既存機能への影響なし（新規メソッド追加のみ）

### データベースへの影響
- **新規テーブル**: `orders`, `order_items`
- **既存テーブルへの変更**: なし
- **マイグレーション**: 必要

### APIへの影響
- **新規エンドポイント**: 4つ（POST /orders, GET /orders/{id}, PUT /orders/{id}/status, POST /orders/{id}/cancel）
- **既存エンドポイントへの影響**: なし

### 永続的ドキュメント（docs/）への影響
**影響**: あり

以下のドキュメントに注文機能の追加を反映する必要がある:
- `docs/architecture/` - 技術仕様書（Order境界コンテキスト、ドメインモデル、テーブル定義の追加）
- `docs/repository-structure.md` - リポジトリ構造（backend/app/domain/order, backend/app/application/orderディレクトリの追加）

---

## 実装優先順位

1. **Domain層** - Order集約、値オブジェクト、ドメインサービス
2. **Infrastructure層** - SQLAlchemyモデル、OrderRepository実装
3. **既存コンポーネント変更** - Stock.allocate/release、ProductRepository.find_by_ids
4. **Application層** - ユースケース、DTO
5. **Presentation層** - Pydanticスキーマ、FastAPIエンドポイント
6. **マイグレーション** - Alembicマイグレーションファイル作成
7. **ルーティング設定** - router.pyへの登録

---

## 技術的注意事項

### SQLAlchemy 2.0スタイルの徹底
- `Mapped`、`mapped_column` を使用
- `select()`、`update()` 文を使用（レガシーなQuery APIは使用しない）
- リレーションは `lazy="joined"` でEager Loading

### トランザクション管理
- Application層のUseCaseで `db.commit()` / `db.rollback()` を実行
- Domain層、Infrastructure層ではトランザクション制御を行わない

### バリデーション責務
- **Presentation層（Pydantic）**: 形式バリデーション（型、長さ、正規表現）
- **Domain層（値オブジェクト）**: ビジネスルールバリデーション（ステータス遷移、在庫数）

### イベント駆動設計
- 今回の実装ではドメインイベントの発行のみを行う
- イベントハンドラー（購読者）は別タスクで実装

---

以上が注文エンドポイント実装の設計書です。
