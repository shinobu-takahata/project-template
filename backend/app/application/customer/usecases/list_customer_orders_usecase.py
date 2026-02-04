from app.application.customer.dtos.order_dto import OrderSummaryDTO, PaginationDTO
from app.application.customer.exceptions import CustomerNotFoundError
from app.domain.customer.repositories.customer_repository import ICustomerRepository
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.product.repositories.order_repository import IOrderRepository


class ListCustomerOrdersUseCase:
    """顧客注文履歴取得ユースケース（スタブ実装）"""

    def __init__(
        self,
        customer_repository: ICustomerRepository,
        order_repository: IOrderRepository,
    ):
        self.customer_repository = customer_repository
        self.order_repository = order_repository

    def execute(
        self,
        customer_id: str,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[OrderSummaryDTO], PaginationDTO]:
        # 顧客の存在確認
        customer = self.customer_repository.find_by_id(CustomerId(customer_id))
        if customer is None:
            raise CustomerNotFoundError(
                f"Customer with ID '{customer_id}' not found"
            )

        # 注文一覧を取得（スタブ実装なので空リスト）
        orders, total = self.order_repository.find_by_customer_id(
            customer_id, status, page, per_page
        )

        order_dtos: list[OrderSummaryDTO] = []
        pagination = PaginationDTO(total=total, page=page, per_page=per_page)

        return order_dtos, pagination
