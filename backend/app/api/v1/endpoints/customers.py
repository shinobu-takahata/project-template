from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.application.customer.dtos.customer_dto import (
    AddShippingAddressInputDTO,
    RegisterCustomerInputDTO,
    ShippingAddressDTO,
    UpdateCustomerInputDTO,
)
from app.application.customer.exceptions import (
    CustomerNotFoundError,
    DuplicateEmailError,
)
from app.application.customer.usecases.add_shipping_address_usecase import (
    AddShippingAddressUseCase,
)
from app.application.customer.usecases.get_customer_usecase import (
    GetCustomerUseCase,
)
from app.application.customer.usecases.list_customer_orders_usecase import (
    ListCustomerOrdersUseCase,
)
from app.application.customer.usecases.list_customers_usecase import (
    ListCustomersUseCase,
)
from app.application.customer.usecases.register_customer_usecase import (
    RegisterCustomerUseCase,
)
from app.application.customer.usecases.update_customer_usecase import (
    UpdateCustomerUseCase,
)
from app.core.database import get_db
from app.infrastructure.repositories.customer_repository import CustomerRepository
from app.infrastructure.repositories.order_repository import OrderRepository
from app.schemas.customer import (
    AddressResponse,
    CustomerOrderListResponse,
    CustomerRegisterRequest,
    CustomerResponse,
    CustomerUpdateRequest,
    OrderSummaryResponse,
    PaginationResponse,
    ShippingAddressAddRequest,
    ShippingAddressResponse,
)

router = APIRouter()


def _to_address_response(dto: ShippingAddressDTO) -> ShippingAddressResponse:
    return ShippingAddressResponse(
        id=dto.address_id,
        label=dto.label,
        address=AddressResponse(
            postal_code=dto.postal_code,
            prefecture=dto.prefecture,
            city=dto.city,
            street=dto.street,
        ),
        is_default=dto.is_default,
    )


def _to_customer_response(dto) -> CustomerResponse:
    return CustomerResponse(
        id=dto.customer_id,
        name=dto.name,
        email=dto.email,
        member_rank=dto.member_rank,
        shipping_addresses=[_to_address_response(addr) for addr in dto.shipping_addresses],
        created_at=dto.created_at,
    )


@router.get("", response_model=list[CustomerResponse])
def list_customers(db: Session = Depends(get_db)):
    """顧客一覧取得"""
    customer_repository = CustomerRepository(db)
    usecase = ListCustomersUseCase(customer_repository)
    customer_dtos = usecase.execute()
    return [_to_customer_response(dto) for dto in customer_dtos]


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
):
    """顧客情報取得"""
    customer_repository = CustomerRepository(db)
    usecase = GetCustomerUseCase(customer_repository)

    try:
        return _to_customer_response(usecase.execute(customer_id))
    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def register_customer(
    request: CustomerRegisterRequest,
    db: Session = Depends(get_db),
):
    """顧客登録"""
    customer_repository = CustomerRepository(db)
    usecase = RegisterCustomerUseCase(customer_repository, db)

    input_dto = RegisterCustomerInputDTO(
        name=request.name,
        email=request.email,
        shipping_address={
            "label": request.shipping_address.label,
            "postal_code": request.shipping_address.postal_code,
            "prefecture": request.shipping_address.prefecture,
            "city": request.shipping_address.city,
            "street": request.shipping_address.street,
        },
    )

    try:
        return _to_customer_response(usecase.execute(input_dto))
    except DuplicateEmailError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: str,
    request: CustomerUpdateRequest,
    db: Session = Depends(get_db),
):
    """顧客情報更新"""
    customer_repository = CustomerRepository(db)
    usecase = UpdateCustomerUseCase(customer_repository, db)

    input_dto = UpdateCustomerInputDTO(
        name=request.name,
        email=request.email,
    )

    try:
        return _to_customer_response(usecase.execute(customer_id, input_dto))
    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicateEmailError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{customer_id}/addresses",
    response_model=ShippingAddressResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_shipping_address(
    customer_id: str,
    request: ShippingAddressAddRequest,
    db: Session = Depends(get_db),
):
    """配送先住所追加"""
    customer_repository = CustomerRepository(db)
    usecase = AddShippingAddressUseCase(customer_repository, db)

    input_dto = AddShippingAddressInputDTO(
        label=request.label,
        postal_code=request.postal_code,
        prefecture=request.prefecture,
        city=request.city,
        street=request.street,
        is_default=request.is_default,
    )

    try:
        address_dto = usecase.execute(customer_id, input_dto)
        return _to_address_response(address_dto)
    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{customer_id}/orders", response_model=CustomerOrderListResponse)
def list_customer_orders(
    customer_id: str,
    order_status: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """顧客注文履歴取得（スタブ実装）"""
    customer_repository = CustomerRepository(db)
    order_repository = OrderRepository(db)
    usecase = ListCustomerOrdersUseCase(customer_repository, order_repository)

    try:
        order_dtos, pagination_dto = usecase.execute(customer_id, order_status, page, per_page)

        return CustomerOrderListResponse(
            data=[OrderSummaryResponse(**dto.__dict__) for dto in order_dtos],
            pagination=PaginationResponse(**pagination_dto.__dict__),
        )
    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
