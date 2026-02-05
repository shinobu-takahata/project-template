from sqlalchemy.orm import Session

from app.application.order.dtos.order_dto import OrderCancelDTO
from app.application.order.exceptions import (
    OrderCannotBeCancelledError,
    OrderNotFoundError,
)
from app.domain.order.exceptions import (
    OrderCannotBeCancelledError as DomainOrderCannotBeCancelledError,
)
from app.domain.order.repositories.order_repository import IOrderRepository
from app.domain.order.value_objects.order_id import OrderId
from app.domain.stock.repositories.stock_repository import IStockRepository


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
            raise OrderNotFoundError(
                f"Order with ID '{order_id}' not found"
            )

        try:
            order.cancel(reason)
        except DomainOrderCannotBeCancelledError as e:
            raise OrderCannotBeCancelledError(str(e))

        # 在庫を戻す
        try:
            for item in order.items:
                stock = self.stock_repository.find_by_product_id(item.product_id)
                if stock is not None:
                    stock.release(item.quantity)
                    self.stock_repository.save(stock)

            self.order_repository.save(order)
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
