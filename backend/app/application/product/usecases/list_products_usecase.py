from app.application.product.dtos.product_dto import PaginationDTO, ProductDTO
from app.domain.product.repositories.product_repository import IProductRepository


class ListProductsUseCase:
    """商品一覧取得ユースケース"""

    def __init__(self, product_repository: IProductRepository):
        self.product_repository = product_repository

    def execute(
        self,
        category: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[ProductDTO], PaginationDTO]:
        products, total = self.product_repository.find_all(category, page, per_page)

        product_dtos = [
            ProductDTO(
                id=p.id.value,
                name=p.name.value,
                sku=p.sku.value,
                price=p.price.value,
                category=p.category,
                description=p.description,
                stock_quantity=0,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in products
        ]

        pagination = PaginationDTO(total=total, page=page, per_page=per_page)

        return product_dtos, pagination
