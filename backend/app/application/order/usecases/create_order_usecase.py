from sqlalchemy.orm import Session

from app.application.order.dtos.order_dto import CreateOrderInputDTO, OrderDTO
from app.application.order.exceptions import (
    CustomerNotFoundError,
    InsufficientStockError,
    InvalidShippingAddressError,
    ProductNotFoundError,
)
from app.domain.customer.repositories.customer_repository import (
    ICustomerRepository,
)
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.order.repositories.order_repository import IOrderRepository
from app.domain.order.services.order_domain_service import OrderDomainService
from app.domain.order.value_objects.shipping_address import ShippingAddress
from app.domain.product.repositories.product_repository import (
    IProductRepository,
)
from app.domain.product.value_objects.product_id import ProductId
from app.domain.stock.repositories.stock_repository import IStockRepository


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
                f"Shipping address '{input_dto.shipping_address_id}' "
                "not found for this customer"
            )

        shipping_address = ShippingAddress(
            postal_code=shipping_address_entity.address.postal_code,
            prefecture=shipping_address_entity.address.prefecture,
            city=shipping_address_entity.address.city,
            street=shipping_address_entity.address.street,
        )

        # 商品情報取得
        product_ids = [
            ProductId(item.product_id) for item in input_dto.items
        ]
        products = self.product_repository.find_by_ids(product_ids)

        if len(products) != len(product_ids):
            raise ProductNotFoundError("One or more products not found")

        # 在庫確認と引当
        quantities = {
            item.product_id: item.quantity for item in input_dto.items
        }
        stocks = []
        for product in products:
            stock = self.stock_repository.find_by_product_id(product.id)
            if stock is None:
                raise InsufficientStockError(
                    f"Stock for product '{product.id.value}' not found"
                )

            quantity = quantities.get(product.id.value, 0)
            try:
                stock.allocate(quantity)
            except ValueError as e:
                raise InsufficientStockError(str(e))

            stocks.append(stock)

        # ドメインサービスで注文生成
        order = OrderDomainService.create_order(
            customer=customer,
            products=products,
            quantities=quantities,
            shipping_address=shipping_address,
            coupon_code=input_dto.coupon_code,
        )

        # 永続化
        self.order_repository.save(order)
        for stock in stocks:
            self.stock_repository.save(stock)
        self.db.commit()

        return OrderDTO.from_entity(order)
