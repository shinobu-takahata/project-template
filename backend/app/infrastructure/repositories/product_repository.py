from sqlalchemy import func, select, update
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
        stmt = select(ProductModel).where(
            ProductModel.id == product_id.value,
            ProductModel.deleted_at.is_(None),
        )
        model = self.db.scalars(stmt).first()

        if model is None:
            return None

        return self._to_entity(model)

    def find_by_sku(self, sku: SKU) -> Product | None:
        stmt = select(ProductModel).where(
            ProductModel.sku == sku.value,
            ProductModel.deleted_at.is_(None),
        )
        model = self.db.scalars(stmt).first()

        if model is None:
            return None

        return self._to_entity(model)

    def find_all(
        self,
        category: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Product], int]:
        stmt = select(ProductModel).where(
            ProductModel.deleted_at.is_(None),
        )

        if category:
            stmt = stmt.where(ProductModel.category == category)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)
        models = self.db.scalars(stmt).all()

        products = [self._to_entity(m) for m in models]
        return products, total

    def save(self, product: Product) -> None:
        exists = self.db.scalar(
            select(ProductModel.id).where(ProductModel.id == product.id.value)
        )

        if exists is None:
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
            stmt = (
                update(ProductModel)
                .where(ProductModel.id == product.id.value)
                .values(
                    name=product.name.value,
                    price=product.price.value,
                    category=product.category,
                    description=product.description,
                    deleted_at=product.deleted_at,
                    updated_at=product.updated_at,
                )
            )
            self.db.execute(stmt)

        self.db.flush()

    def find_by_ids(self, product_ids: list[ProductId]) -> list[Product]:
        stmt = select(ProductModel).where(
            ProductModel.id.in_([pid.value for pid in product_ids]),
            ProductModel.deleted_at.is_(None),
        )
        models = self.db.scalars(stmt).all()
        return [self._to_entity(m) for m in models]

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
