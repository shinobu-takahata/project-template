from sqlalchemy.orm import Session

from app.application.order.dtos.order_dto import OrderStatusUpdateDTO
from app.application.order.exceptions import (
    InvalidStatusTransitionError,
    OrderNotFoundError,
)
from app.domain.order.exceptions import (
    InvalidStatusTransitionError as DomainInvalidStatusTransitionError,
)
from app.domain.order.repositories.order_repository import IOrderRepository
from app.domain.order.value_objects.order_id import OrderId
from app.domain.order.value_objects.order_status import OrderStatus


class UpdateOrderStatusUseCase:
    """注文ステータス更新ユースケース"""

    def __init__(self, order_repository: IOrderRepository, db: Session):
        self.order_repository = order_repository
        self.db = db

    def execute(
        self, order_id: str, new_status: str
    ) -> OrderStatusUpdateDTO:
        order = self.order_repository.find_by_id(OrderId(order_id))
        if order is None:
            raise OrderNotFoundError(
                f"Order with ID '{order_id}' not found"
            )

        previous_status = order.status.value

        try:
            order.transition_to(OrderStatus(new_status))
        except DomainInvalidStatusTransitionError as e:
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
