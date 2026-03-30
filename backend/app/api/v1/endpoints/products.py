from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.application.product.dtos.product_dto import (
    RegisterProductInputDTO,
    UpdateProductInputDTO,
)
from app.application.product.exceptions import (
    DuplicateSKUError,
    ProductInUseError,
    ProductNotFoundError,
)
from app.application.product.usecases.delete_product_usecase import (
    DeleteProductUseCase,
)
from app.application.product.usecases.list_products_usecase import (
    ListProductsUseCase,
)
from app.application.product.usecases.register_product_usecase import (
    RegisterProductUseCase,
)
from app.application.product.usecases.update_product_usecase import (
    UpdateProductUseCase,
)
from app.core.database import get_db
from app.infrastructure.repositories.order_repository import OrderRepository
from app.infrastructure.repositories.product_repository import ProductRepository
from app.infrastructure.repositories.stock_repository import StockRepository
from app.schemas.product import (
    PaginationResponse,
    ProductCreateRequest,
    ProductListResponse,
    ProductResponse,
    ProductUpdateRequest,
)

router = APIRouter()


@router.get("/", response_model=ProductListResponse)
def list_products(
    category: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """商品一覧取得"""
    product_repository = ProductRepository(db)
    usecase = ListProductsUseCase(product_repository)

    product_dtos, pagination_dto = usecase.execute(category, page, per_page)

    return ProductListResponse(
        data=[ProductResponse(**dto.__dict__) for dto in product_dtos],
        pagination=PaginationResponse(**pagination_dto.__dict__),
    )


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def register_product(
    request: ProductCreateRequest,
    db: Session = Depends(get_db),
):
    """商品登録"""
    product_repository = ProductRepository(db)
    stock_repository = StockRepository(db)
    usecase = RegisterProductUseCase(product_repository, stock_repository, db)

    input_dto = RegisterProductInputDTO(
        name=request.name,
        sku=request.sku,
        price=request.price,
        category=request.category,
        description=request.description,
        initial_stock=request.initial_stock,
    )

    try:
        product_dto = usecase.execute(input_dto)
        return ProductResponse(**product_dto.__dict__)
    except DuplicateSKUError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: str,
    request: ProductUpdateRequest,
    db: Session = Depends(get_db),
):
    """商品更新"""
    product_repository = ProductRepository(db)
    usecase = UpdateProductUseCase(product_repository, db)

    input_dto = UpdateProductInputDTO(
        name=request.name,
        price=request.price,
        category=request.category,
        description=request.description,
    )

    try:
        product_dto = usecase.execute(product_id, input_dto)
        return ProductResponse(**product_dto.__dict__)
    except ProductNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
):
    """商品削除"""
    product_repository = ProductRepository(db)
    order_repository = OrderRepository(db)
    usecase = DeleteProductUseCase(product_repository, order_repository, db)

    try:
        usecase.execute(product_id)
    except ProductNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except ProductInUseError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
