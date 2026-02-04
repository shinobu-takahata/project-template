from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.application.order.dtos.order_dto import (
    CreateOrderInputDTO,
    OrderItemInputDTO,
)
from app.application.order.exceptions import (
    CustomerNotFoundError,
    InsufficientStockError,
    InvalidShippingAddressError,
    InvalidStatusTransitionError,
    OrderCannotBeCancelledError,
    OrderNotFoundError,
    ProductNotFoundError,
)
from app.application.order.usecases.cancel_order_usecase import (
    CancelOrderUseCase,
)
from app.application.order.usecases.create_order_usecase import (
    CreateOrderUseCase,
)
from app.application.order.usecases.get_order_usecase import GetOrderUseCase
from app.application.order.usecases.update_order_status_usecase import (
    UpdateOrderStatusUseCase,
)
from app.core.database import get_db
from app.infrastructure.repositories.customer_repository import (
    CustomerRepository,
)
from app.infrastructure.repositories.order_repository import OrderRepository
from app.infrastructure.repositories.product_repository import (
    ProductRepository,
)
from app.infrastructure.repositories.stock_repository import StockRepository
from app.schemas.order import (
    OrderCancelDataResponse,
    OrderCancelRequest,
    OrderCancelResponse,
    OrderCreateRequest,
    OrderDataResponse,
    OrderItemResponse,
    OrderResponse,
    OrderStatusDataResponse,
    OrderStatusUpdateRequest,
    OrderStatusUpdateResponse,
    ShippingAddressResponse,
)

router = APIRouter()


@router.post(
    "/",
    response_model=OrderDataResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    request: OrderCreateRequest,
    db: Session = Depends(get_db),
):
    """注文作成"""
    usecase = CreateOrderUseCase(
        customer_repository=CustomerRepository(db),
        product_repository=ProductRepository(db),
        stock_repository=StockRepository(db),
        order_repository=OrderRepository(db),
        db=db,
    )

    input_dto = CreateOrderInputDTO(
        customer_id=request.customer_id,
        shipping_address_id=request.shipping_address_id,
        items=[
            OrderItemInputDTO(
                product_id=item.product_id, quantity=item.quantity
            )
            for item in request.items
        ],
        coupon_code=request.coupon_code,
    )

    try:
        order_dto = usecase.execute(input_dto)
    except CustomerNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except ProductNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except InsufficientStockError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except InvalidShippingAddressError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    return OrderDataResponse(
        data=OrderResponse(
            order_id=order_dto.order_id,
            status=order_dto.status,
            customer_id=order_dto.customer_id,
            items=[
                OrderItemResponse(**item.__dict__)
                for item in order_dto.items
            ],
            subtotal=order_dto.subtotal,
            discount_amount=order_dto.discount_amount,
            tax_amount=order_dto.tax_amount,
            shipping_fee=order_dto.shipping_fee,
            total_amount=order_dto.total_amount,
            shipping_address=ShippingAddressResponse(
                **order_dto.shipping_address.__dict__
            ),
            ordered_at=order_dto.ordered_at,
        )
    )


@router.get("/{order_id}", response_model=OrderDataResponse)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
):
    """注文詳細取得"""
    usecase = GetOrderUseCase(order_repository=OrderRepository(db))

    try:
        order_dto = usecase.execute(order_id)
    except OrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )

    return OrderDataResponse(
        data=OrderResponse(
            order_id=order_dto.order_id,
            status=order_dto.status,
            customer_id=order_dto.customer_id,
            items=[
                OrderItemResponse(**item.__dict__)
                for item in order_dto.items
            ],
            subtotal=order_dto.subtotal,
            discount_amount=order_dto.discount_amount,
            tax_amount=order_dto.tax_amount,
            shipping_fee=order_dto.shipping_fee,
            total_amount=order_dto.total_amount,
            shipping_address=ShippingAddressResponse(
                **order_dto.shipping_address.__dict__
            ),
            ordered_at=order_dto.ordered_at,
        )
    )


@router.put(
    "/{order_id}/status", response_model=OrderStatusDataResponse
)
def update_order_status(
    order_id: str,
    request: OrderStatusUpdateRequest,
    db: Session = Depends(get_db),
):
    """注文ステータス更新"""
    usecase = UpdateOrderStatusUseCase(
        order_repository=OrderRepository(db), db=db
    )

    try:
        status_dto = usecase.execute(order_id, request.status)
    except OrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    return OrderStatusDataResponse(
        data=OrderStatusUpdateResponse(**status_dto.__dict__)
    )


@router.post(
    "/{order_id}/cancel", response_model=OrderCancelDataResponse
)
def cancel_order(
    order_id: str,
    request: OrderCancelRequest,
    db: Session = Depends(get_db),
):
    """注文キャンセル"""
    usecase = CancelOrderUseCase(
        order_repository=OrderRepository(db),
        stock_repository=StockRepository(db),
        db=db,
    )

    try:
        cancel_dto = usecase.execute(order_id, request.reason)
    except OrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except OrderCannotBeCancelledError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )

    return OrderCancelDataResponse(
        data=OrderCancelResponse(**cancel_dto.__dict__)
    )
