from app.domain.product.entities.product import Product
from app.domain.product.repositories.product_repository import IProductRepository
from app.domain.product.value_objects.product_id import ProductId
from app.domain.product.value_objects.sku import SKU


class MockProductRepository(IProductRepository):
    """テスト用モック商品リポジトリ"""

    def __init__(self):
        self.products: dict[str, Product] = {}

    def find_by_id(self, product_id: ProductId) -> Product | None:
        product = self.products.get(product_id.value)
        if product and product.deleted_at is None:
            return product
        return None

    def find_by_sku(self, sku: SKU) -> Product | None:
        for product in self.products.values():
            if product.sku.value == sku.value and product.deleted_at is None:
                return product
        return None

    def find_all(
        self,
        category: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Product], int]:
        active = [p for p in self.products.values() if p.deleted_at is None]

        if category:
            active = [p for p in active if p.category == category]

        total = len(active)
        offset = (page - 1) * per_page
        paginated = active[offset : offset + per_page]

        return paginated, total

    def save(self, product: Product) -> None:
        self.products[product.id.value] = product
