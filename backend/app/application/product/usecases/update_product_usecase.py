from sqlalchemy.orm import Session

from app.application.product.dtos.product_dto import ProductDTO, UpdateProductInputDTO
from app.application.product.exceptions import ProductNotFoundError
from app.domain.product.repositories.product_repository import IProductRepository
from app.domain.product.value_objects.price import Price
from app.domain.product.value_objects.product_id import ProductId
from app.domain.product.value_objects.product_name import ProductName


class UpdateProductUseCase:
    """商品更新ユースケース"""

    def __init__(self, product_repository: IProductRepository, db: Session):
        self.product_repository = product_repository
        self.db = db

    def execute(self, product_id: str, input_dto: UpdateProductInputDTO) -> ProductDTO:
        product = self.product_repository.find_by_id(ProductId(product_id))
        if product is None:
            raise ProductNotFoundError(
                f"Product with ID '{product_id}' not found"
            )

        product.update(
            name=ProductName(input_dto.name),
            price=Price(input_dto.price),
            category=input_dto.category,
            description=input_dto.description,
        )

        try:
            self.product_repository.save(product)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

        return ProductDTO(
            id=product.id.value,
            name=product.name.value,
            sku=product.sku.value,
            price=product.price.value,
            category=product.category,
            description=product.description,
            stock_quantity=0,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )
