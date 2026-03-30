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
            raise OrderNotFoundError(
                f"Order with ID '{order_id}' not found"
            )

        return OrderDTO.from_entity(order)
