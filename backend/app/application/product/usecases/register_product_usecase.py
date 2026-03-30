from sqlalchemy.orm import Session

from app.application.product.dtos.product_dto import ProductDTO, RegisterProductInputDTO
from app.application.product.exceptions import DuplicateSKUError
from app.domain.product.entities.product import Product
from app.domain.product.repositories.product_repository import IProductRepository
from app.domain.product.value_objects.price import Price
from app.domain.product.value_objects.product_name import ProductName
from app.domain.product.value_objects.sku import SKU
from app.domain.stock.entities.stock import Stock
from app.domain.stock.repositories.stock_repository import IStockRepository
from app.domain.stock.value_objects.stock_quantity import StockQuantity


class RegisterProductUseCase:
    """商品登録ユースケース"""

    def __init__(
        self,
        product_repository: IProductRepository,
        stock_repository: IStockRepository,
        db: Session,
    ):
        self.product_repository = product_repository
        self.stock_repository = stock_repository
        self.db = db

    def execute(self, input_dto: RegisterProductInputDTO) -> ProductDTO:
        existing = self.product_repository.find_by_sku(SKU(input_dto.sku))
        if existing is not None:
            raise DuplicateSKUError(f"SKU '{input_dto.sku}' already exists")

        product = Product.create(
            name=ProductName(input_dto.name),
            sku=SKU(input_dto.sku),
            price=Price(input_dto.price),
            category=input_dto.category,
            description=input_dto.description,
        )

        stock = Stock.initialize(
            product_id=product.id,
            quantity=StockQuantity(input_dto.initial_stock),
        )

        try:
            self.product_repository.save(product)
            self.stock_repository.save(stock)
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
            stock_quantity=stock.quantity.value,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )
