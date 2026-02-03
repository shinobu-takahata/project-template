from sqlalchemy.orm import Session

from app.domain.product.entities.product import Product
from app.domain.product.repositories.product_repository import IProductRepository
from app.domain.product.value_objects.price import Price
from app.domain.product.value_objects.product_id import ProductId
from app.domain.product.value_objects.product_name import ProductName
from app.domain.product.value_objects.sku import SKU
from app.infrastructure.database.models import ProductModel


class ProductRepository(IProductRepository):
    """商品リポジトリ実装"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, product_id: ProductId) -> Product | None:
        model = self.db.query(ProductModel).filter(
            ProductModel.id == product_id.value,
            ProductModel.deleted_at.is_(None),
        ).first()

        if model is None:
            return None

        return self._to_entity(model)

    def find_by_sku(self, sku: SKU) -> Product | None:
        model = self.db.query(ProductModel).filter(
            ProductModel.sku == sku.value,
            ProductModel.deleted_at.is_(None),
        ).first()

        if model is None:
            return None

        return self._to_entity(model)

    def find_all(
        self,
        category: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Product], int]:
        query = self.db.query(ProductModel).filter(
            ProductModel.deleted_at.is_(None),
        )

        if category:
            query = query.filter(ProductModel.category == category)

        total = query.count()

        offset = (page - 1) * per_page
        models = query.offset(offset).limit(per_page).all()

        products = [self._to_entity(m) for m in models]
        return products, total

    def save(self, product: Product) -> None:
        model = self.db.query(ProductModel).filter(
            ProductModel.id == product.id.value,
        ).first()

        if model is None:
            model = ProductModel(
                id=product.id.value,
                name=product.name.value,
                sku=product.sku.value,
                price=product.price.value,
                category=product.category,
                description=product.description,
                deleted_at=product.deleted_at,
                created_at=product.created_at,
                updated_at=product.updated_at,
            )
            self.db.add(model)
        else:
            model.name = product.name.value
            model.price = product.price.value
            model.category = product.category
            model.description = product.description
            model.deleted_at = product.deleted_at
            model.updated_at = product.updated_at

        self.db.flush()

    def _to_entity(self, model: ProductModel) -> Product:
        return Product(
            id=ProductId(model.id),
            name=ProductName(model.name),
            sku=SKU(model.sku),
            price=Price(model.price),
            category=model.category,
            description=model.description,
            deleted_at=model.deleted_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
