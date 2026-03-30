from app.application.product.usecases.list_products_usecase import ListProductsUseCase
from app.domain.product.entities.product import Product
from app.domain.product.value_objects.price import Price
from app.domain.product.value_objects.product_name import ProductName
from app.domain.product.value_objects.sku import SKU
from tests.unit.mocks.mock_product_repository import MockProductRepository


class TestListProductsUseCase:
    def _create_usecase(self, repository: MockProductRepository):
        return ListProductsUseCase(repository)

    def test_list_empty(self):
        repo = MockProductRepository()
        usecase = self._create_usecase(repo)

        products, pagination = usecase.execute()

        assert len(products) == 0
        assert pagination.total == 0

    def test_list_products(self):
        repo = MockProductRepository()
        product = Product.create(
            name=ProductName("Test"),
            sku=SKU("SKU-001"),
            price=Price(1000),
            category="Test",
        )
        repo.save(product)

        usecase = self._create_usecase(repo)
        products, pagination = usecase.execute()

        assert len(products) == 1
        assert products[0].name == "Test"
        assert pagination.total == 1

    def test_list_with_category_filter(self):
        repo = MockProductRepository()
        p1 = Product.create(
            name=ProductName("Mouse"),
            sku=SKU("M-001"),
            price=Price(1000),
            category="PC周辺機器",
        )
        p2 = Product.create(
            name=ProductName("Keyboard"),
            sku=SKU("K-001"),
            price=Price(2000),
            category="PC周辺機器",
        )
        p3 = Product.create(
            name=ProductName("Desk"),
            sku=SKU("D-001"),
            price=Price(5000),
            category="家具",
        )
        repo.save(p1)
        repo.save(p2)
        repo.save(p3)

        usecase = self._create_usecase(repo)
        products, pagination = usecase.execute(category="PC周辺機器")

        assert len(products) == 2
        assert pagination.total == 2

    def test_list_with_pagination(self):
        repo = MockProductRepository()
        for i in range(5):
            p = Product.create(
                name=ProductName(f"Product {i}"),
                sku=SKU(f"SKU-{i:03d}"),
                price=Price(1000),
                category="Test",
            )
            repo.save(p)

        usecase = self._create_usecase(repo)
        products, pagination = usecase.execute(page=1, per_page=2)

        assert len(products) == 2
        assert pagination.total == 5
        assert pagination.page == 1
        assert pagination.per_page == 2

    def test_deleted_products_not_listed(self):
        repo = MockProductRepository()
        product = Product.create(
            name=ProductName("Test"),
            sku=SKU("SKU-001"),
            price=Price(1000),
            category="Test",
        )
        product.delete()
        repo.save(product)

        usecase = self._create_usecase(repo)
        products, pagination = usecase.execute()

        assert len(products) == 0
        assert pagination.total == 0
