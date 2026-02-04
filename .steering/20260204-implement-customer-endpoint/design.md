# 設計書: 顧客エンドポイント実装

## 概要
OrderHub（注文管理システム）の顧客エンドポイントをDDDレイヤードアーキテクチャに基づいて実装する。
既に実装済みの商品エンドポイントと同じアーキテクチャパターンに従い、4つの層（Presentation / Application / Domain / Infrastructure）を明確に分離する。

顧客集約の特徴として、配送先住所（ShippingAddress）を集約内エンティティとして管理し、Customer経由でのみアクセス可能とする。

## 実装アプローチ

### アーキテクチャ方針
1. **DDDレイヤードアーキテクチャ**: 既存の `backend/app` ディレクトリ構造を活用し、各層の責務を明確に分離する
2. **依存性逆転の原則**: Domain層にリポジトリインターフェースを定義し、Infrastructure層で実装する
3. **純粋なドメインモデル**: Domain層は外部ライブラリ（FastAPI、SQLAlchemy等）に依存しない
4. **トランザクション境界**: Application層（UseCase）でトランザクションを制御する
5. **値オブジェクトによるバリデーション**: コンストラクタで不変条件を検証し、不正な値の生成を防ぐ
6. **集約内エンティティの管理**: ShippingAddressは独自リポジトリを持たず、Customer経由でのみアクセス

### 実装順序
1. Domain層の実装（値オブジェクト → エンティティ → リポジトリIF → ドメイン例外）
2. Infrastructure層の実装（SQLAlchemyモデル → リポジトリ実装 → Alembicマイグレーション）
3. Application層の実装（DTO → UseCase）
4. Presentation層の実装（Pydanticスキーマ → FastAPIルーター → エラーハンドラ）
5. 各層のテスト実装

---

## ディレクトリ構造

### 新規作成するファイル

```
backend/app/
├── domain/
│   ├── customer/                          # 新規: 顧客集約
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── customer.py                # 顧客エンティティ（集約ルート）
│   │   │   └── shipping_address.py        # 配送先住所エンティティ（集約内）
│   │   ├── value_objects/
│   │   │   ├── __init__.py
│   │   │   ├── customer_id.py             # 顧客ID
│   │   │   ├── customer_name.py           # 顧客名
│   │   │   ├── email_address.py           # メールアドレス
│   │   │   ├── member_rank.py             # 会員ランク
│   │   │   └── address.py                 # 住所
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── customer_repository.py     # Customerリポジトリインターフェース
│   │   └── exceptions.py                  # 顧客ドメイン例外
│   └── order/                              # 新規: 注文集約（スタブ実装用の最小定義）
│       ├── __init__.py
│       ├── repositories/
│       │   ├── __init__.py
│       │   └── order_repository.py         # Orderリポジトリインターフェース（顧客注文履歴用）
├── application/
│   └── customer/                           # 新規: 顧客ユースケース
│       ├── __init__.py
│       ├── dtos/
│       │   ├── __init__.py
│       │   ├── customer_dto.py             # 顧客DTO（UseCase層の入出力）
│       │   └── order_dto.py                # 注文DTO（注文履歴用）
│       ├── usecases/
│       │   ├── __init__.py
│       │   ├── get_customer_usecase.py     # GET /api/v1/customers/{id}
│       │   ├── register_customer_usecase.py # POST /api/v1/customers
│       │   ├── update_customer_usecase.py  # PUT /api/v1/customers/{id}
│       │   ├── add_shipping_address_usecase.py # POST /api/v1/customers/{id}/addresses
│       │   └── list_customer_orders_usecase.py # GET /api/v1/customers/{id}/orders
│       └── exceptions.py                   # Application層例外
├── infrastructure/
│   ├── database/
│   │   └── models.py                       # 変更: 顧客・配送先住所テーブルモデル追加
│   └── repositories/
│       ├── customer_repository.py          # 新規: Customerリポジトリ実装
│       └── order_repository.py             # 変更: 顧客注文履歴用メソッド追加（スタブ）
├── api/v1/
│   └── endpoints/
│       └── customers.py                    # 新規: 顧客エンドポイント
├── schemas/
│   └── customer.py                         # 新規: 顧客Pydanticスキーマ

alembic/
└── versions/
    └── YYYYMMDD_create_customers_and_shipping_addresses.py  # 新規: マイグレーション

tests/
├── unit/
│   ├── domain/
│   │   └── customer/
│   │       ├── test_customer_entity.py         # 顧客エンティティのテスト
│   │       ├── test_customer_value_objects.py  # 値オブジェクトのテスト
│   │       └── test_shipping_address_entity.py # 配送先住所エンティティのテスト
│   ├── application/
│   │   └── customer/
│   │       ├── test_get_customer_usecase.py
│   │       ├── test_register_customer_usecase.py
│   │       ├── test_update_customer_usecase.py
│   │       ├── test_add_shipping_address_usecase.py
│   │       └── test_list_customer_orders_usecase.py
│   └── mocks/
│       ├── mock_customer_repository.py
│       └── mock_order_repository.py (既存に追加)
└── integration/
    └── api/
        └── v1/
            └── test_customers_endpoint.py        # APIエンドポイントの統合テスト
```

---

## 各層の詳細設計

## 1. Domain層（ドメイン層）

### 1.1 値オブジェクト

#### CustomerId (`domain/customer/value_objects/customer_id.py`)
```python
from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class CustomerId:
    """顧客ID値オブジェクト"""
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("CustomerId cannot be empty")

    @staticmethod
    def generate() -> "CustomerId":
        """新しい顧客IDを生成する"""
        return CustomerId(str(uuid.uuid4()))
```

**設計判断:**
- 商品IDと同じパターン（UUID生成、不変性、バリデーション）

#### CustomerName (`domain/customer/value_objects/customer_name.py`)
```python
from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerName:
    """顧客名値オブジェクト"""
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("CustomerName cannot be empty")
        if len(self.value) > 100:
            raise ValueError("CustomerName must be 100 characters or less")
```

**設計判断:**
- 1文字以上100文字以下

#### EmailAddress (`domain/customer/value_objects/email_address.py`)
```python
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class EmailAddress:
    """メールアドレス値オブジェクト"""
    value: str

    # RFC 5322準拠の簡易パターン
    PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("EmailAddress cannot be empty")
        if len(self.value) > 255:
            raise ValueError("EmailAddress must be 255 characters or less")
        if not self.PATTERN.match(self.value):
            raise ValueError(f"Invalid email format: {self.value}")
```

**設計判断:**
- RFC準拠のパターンマッチングでフォーマット検証
- ビジネスルール（メールアドレス形式）をドメイン層で表現

#### MemberRank (`domain/customer/value_objects/member_rank.py`)
```python
from enum import Enum


class MemberRank(str, Enum):
    """会員ランク値オブジェクト"""
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"

    @staticmethod
    def default() -> "MemberRank":
        """デフォルトランクを返す"""
        return MemberRank.BRONZE
```

**設計判断:**
- Enumで列挙型として定義
- 初期値BRONZEをファクトリメソッドで提供

#### Address (`domain/customer/value_objects/address.py`)
```python
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Address:
    """住所値オブジェクト"""
    postal_code: str  # NNN-NNNN形式
    prefecture: str   # 都道府県
    city: str         # 市区町村
    street: str       # 番地以降

    POSTAL_CODE_PATTERN = re.compile(r"^\d{3}-\d{4}$")

    def __post_init__(self):
        # 郵便番号のフォーマット検証
        if not self.postal_code or not self.POSTAL_CODE_PATTERN.match(self.postal_code):
            raise ValueError(f"Postal code must be in NNN-NNNN format: {self.postal_code}")

        # 各フィールドの空チェック
        if not self.prefecture or len(self.prefecture.strip()) == 0:
            raise ValueError("Prefecture cannot be empty")
        if not self.city or len(self.city.strip()) == 0:
            raise ValueError("City cannot be empty")
        if not self.street or len(self.street.strip()) == 0:
            raise ValueError("Street cannot be empty")

        # 長さチェック
        if len(self.prefecture) > 10:
            raise ValueError("Prefecture must be 10 characters or less")
        if len(self.city) > 100:
            raise ValueError("City must be 100 characters or less")
        if len(self.street) > 200:
            raise ValueError("Street must be 200 characters or less")
```

**設計判断:**
- 4つのフィールドで構成（郵便番号、都道府県、市区町村、番地）
- 郵便番号は「NNN-NNNN」形式をパターンマッチングで検証
- DBでは4カラムに展開して永続化

### 1.2 エンティティ

#### Customer（集約ルート） (`domain/customer/entities/customer.py`)
```python
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Optional

from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.customer.value_objects.customer_name import CustomerName
from app.domain.customer.value_objects.email_address import EmailAddress
from app.domain.customer.value_objects.member_rank import MemberRank
from app.domain.customer.entities.shipping_address import ShippingAddress


@dataclass
class Customer:
    """顧客エンティティ（集約ルート）"""
    id: CustomerId
    name: CustomerName
    email: EmailAddress
    member_rank: MemberRank
    shipping_addresses: list[ShippingAddress] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    MAX_ADDRESSES = 5  # 配送先住所の最大数

    @staticmethod
    def create(
        name: CustomerName,
        email: EmailAddress,
    ) -> "Customer":
        """顧客を生成する（ファクトリメソッド）"""
        now = datetime.now(UTC)
        return Customer(
            id=CustomerId.generate(),
            name=name,
            email=email,
            member_rank=MemberRank.default(),  # 初期値BRONZE
            shipping_addresses=[],
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        name: CustomerName,
        email: EmailAddress,
    ) -> None:
        """顧客情報を更新する"""
        self.name = name
        self.email = email
        self.updated_at = datetime.now(UTC)

    def add_shipping_address(self, address: ShippingAddress) -> None:
        """配送先住所を追加する"""
        # 最大5件の制約チェック
        if len(self.shipping_addresses) >= self.MAX_ADDRESSES:
            raise ValueError(
                f"Cannot add more than {self.MAX_ADDRESSES} shipping addresses"
            )

        # is_default=True の場合、既存のデフォルトを解除
        if address.is_default:
            for existing in self.shipping_addresses:
                existing.is_default = False

        self.shipping_addresses.append(address)
        self.updated_at = datetime.now(UTC)

    def get_shipping_address(self, address_id: str) -> ShippingAddress:
        """指定IDの配送先住所を取得する"""
        for address in self.shipping_addresses:
            if address.id == address_id:
                return address

        raise ValueError(f"Shipping address with ID '{address_id}' not found")

    def get_default_address(self) -> Optional[ShippingAddress]:
        """デフォルト配送先住所を取得する"""
        for address in self.shipping_addresses:
            if address.is_default:
                return address
        return None
```

**設計判断:**
- ファクトリメソッド `create()` で生成ロジックをカプセル化（会員ランクはBRONZE固定）
- 配送先住所の最大5件制約をドメイン層で強制
- `add_shipping_address()` でデフォルト住所の一意性を保証
- 配送先住所は集約内で管理（リスト保持）

#### ShippingAddress（集約内エンティティ） (`domain/customer/entities/shipping_address.py`)
```python
from dataclasses import dataclass, field
from datetime import datetime, UTC
import uuid

from app.domain.customer.value_objects.address import Address


@dataclass
class ShippingAddress:
    """配送先住所エンティティ（Customer集約内）"""
    id: str
    label: str  # "自宅"、"会社"等
    address: Address
    is_default: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def create(
        label: str,
        address: Address,
        is_default: bool = False,
    ) -> "ShippingAddress":
        """配送先住所を生成する（ファクトリメソッド）"""
        now = datetime.now(UTC)
        return ShippingAddress(
            id=str(uuid.uuid4()),
            label=label,
            address=address,
            is_default=is_default,
            created_at=now,
            updated_at=now,
        )
```

**設計判断:**
- 集約内エンティティのため、独自のリポジトリを持たない
- IDはUUID文字列（簡易的にstr型）
- Customer集約経由でのみ作成・アクセス可能

### 1.3 リポジトリインターフェース

#### CustomerRepository (`domain/customer/repositories/customer_repository.py`)
```python
from abc import ABC, abstractmethod
from typing import Optional

from app.domain.customer.entities.customer import Customer
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.customer.value_objects.email_address import EmailAddress


class ICustomerRepository(ABC):
    """顧客リポジトリインターフェース"""

    @abstractmethod
    def find_by_id(self, customer_id: CustomerId) -> Optional[Customer]:
        """IDで顧客を取得する（配送先住所含む）"""
        pass

    @abstractmethod
    def find_by_email(self, email: EmailAddress) -> Optional[Customer]:
        """メールアドレスで顧客を取得する"""
        pass

    @abstractmethod
    def save(self, customer: Customer) -> None:
        """顧客を保存する（作成・更新）"""
        pass
```

**設計判断:**
- `find_by_id()` は配送先住所をEager Loadingで取得
- `save()` メソッドで顧客本体と配送先住所を一括保存

#### OrderRepository（顧客注文履歴用） (`domain/order/repositories/order_repository.py`)
```python
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List

from app.domain.customer.value_objects.customer_id import CustomerId


class IOrderRepository(ABC):
    """注文リポジトリインターフェース"""

    @abstractmethod
    def exists_active_order_with_product(self, product_id: str) -> bool:
        """未完了注文に商品が含まれているか確認する（既存メソッド）"""
        pass

    @abstractmethod
    def find_by_customer_id(
        self,
        customer_id: CustomerId,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[dict], int]:
        """顧客IDで注文一覧を取得する（ページネーション対応）

        Returns:
            Tuple[List[dict], int]: (注文リスト（辞書形式）, 総件数)
        """
        pass
```

**設計判断:**
- 既存の `IOrderRepository` に `find_by_customer_id()` メソッドを追加
- 今回はスタブ実装（空のリストを返す）として実装
- 注文エンドポイント実装時に完全な実装に置き換える

### 1.4 ドメイン例外

#### exceptions.py (`domain/customer/exceptions.py`)
```python
class CustomerDomainError(Exception):
    """顧客ドメイン例外の基底クラス"""
    pass


class MaxAddressLimitExceededError(CustomerDomainError):
    """配送先住所上限超過エラー"""
    pass


class ShippingAddressNotFoundError(CustomerDomainError):
    """配送先住所が見つからないエラー"""
    pass


class InvalidEmailFormatError(CustomerDomainError):
    """不正なメールアドレスフォーマットエラー"""
    pass


class InvalidPostalCodeFormatError(CustomerDomainError):
    """不正な郵便番号フォーマットエラー"""
    pass
```

---

## 2. Infrastructure層（インフラストラクチャ層）

### 2.1 SQLAlchemyモデル

#### models.py（変更） (`infrastructure/database/models.py`)
```python
# 既存のProductModel, StockModelに追加

from sqlalchemy import Column, String, Integer, Text, DateTime, CheckConstraint, Index, Boolean, ForeignKey
from sqlalchemy.orm import relationship


class CustomerModel(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    member_rank = Column(String(20), nullable=False, default="BRONZE")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # 配送先住所とのリレーション（Eager Loadingで使用）
    shipping_addresses = relationship(
        "ShippingAddressModel",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="joined",  # Eager Loading
    )

    __table_args__ = (
        CheckConstraint(
            "member_rank IN ('BRONZE', 'SILVER', 'GOLD')",
            name="check_member_rank"
        ),
        Index("idx_customers_email", "email"),
    )


class ShippingAddressModel(Base):
    __tablename__ = "shipping_addresses"

    id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    label = Column(String(50), nullable=False)
    postal_code = Column(String(10), nullable=False)
    prefecture = Column(String(10), nullable=False)
    city = Column(String(100), nullable=False)
    street = Column(String(200), nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # 顧客とのリレーション
    customer = relationship("CustomerModel", back_populates="shipping_addresses")

    __table_args__ = (
        Index("idx_shipping_addresses_customer_id", "customer_id"),
    )
```

**設計判断:**
- `CustomerModel` と `ShippingAddressModel` のリレーションを定義
- `lazy="joined"` でEager Loadingを設定（N+1問題を回避）
- `cascade="all, delete-orphan"` で顧客削除時に配送先住所も削除
- Address値オブジェクトは4カラムに展開して保存

### 2.2 リポジトリ実装

#### CustomerRepository実装 (`infrastructure/repositories/customer_repository.py`)
```python
from typing import Optional
from sqlalchemy.orm import Session

from app.domain.customer.entities.customer import Customer
from app.domain.customer.entities.shipping_address import ShippingAddress
from app.domain.customer.repositories.customer_repository import ICustomerRepository
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.customer.value_objects.customer_name import CustomerName
from app.domain.customer.value_objects.email_address import EmailAddress
from app.domain.customer.value_objects.member_rank import MemberRank
from app.domain.customer.value_objects.address import Address
from app.infrastructure.database.models import CustomerModel, ShippingAddressModel


class CustomerRepository(ICustomerRepository):
    """顧客リポジトリ実装"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, customer_id: CustomerId) -> Optional[Customer]:
        """IDで顧客を取得する（配送先住所含む）"""
        model = self.db.query(CustomerModel).filter(
            CustomerModel.id == customer_id.value
        ).first()

        if model is None:
            return None

        return self._to_entity(model)

    def find_by_email(self, email: EmailAddress) -> Optional[Customer]:
        """メールアドレスで顧客を取得する"""
        model = self.db.query(CustomerModel).filter(
            CustomerModel.email == email.value
        ).first()

        if model is None:
            return None

        return self._to_entity(model)

    def save(self, customer: Customer) -> None:
        """顧客を保存する"""
        model = self.db.query(CustomerModel).filter(
            CustomerModel.id == customer.id.value
        ).first()

        if model is None:
            # 新規作成
            model = CustomerModel(
                id=customer.id.value,
                name=customer.name.value,
                email=customer.email.value,
                member_rank=customer.member_rank.value,
                created_at=customer.created_at,
                updated_at=customer.updated_at,
            )
            self.db.add(model)
        else:
            # 更新
            model.name = customer.name.value
            model.email = customer.email.value
            model.member_rank = customer.member_rank.value
            model.updated_at = customer.updated_at

        # 既存の配送先住所を削除（再作成方式）
        self.db.query(ShippingAddressModel).filter(
            ShippingAddressModel.customer_id == customer.id.value
        ).delete()

        # 配送先住所を保存
        for address in customer.shipping_addresses:
            address_model = ShippingAddressModel(
                id=address.id,
                customer_id=customer.id.value,
                label=address.label,
                postal_code=address.address.postal_code,
                prefecture=address.address.prefecture,
                city=address.address.city,
                street=address.address.street,
                is_default=address.is_default,
                created_at=address.created_at,
                updated_at=address.updated_at,
            )
            self.db.add(address_model)

        self.db.flush()

    def _to_entity(self, model: CustomerModel) -> Customer:
        """モデルをエンティティに変換する"""
        shipping_addresses = [
            ShippingAddress(
                id=addr.id,
                label=addr.label,
                address=Address(
                    postal_code=addr.postal_code,
                    prefecture=addr.prefecture,
                    city=addr.city,
                    street=addr.street,
                ),
                is_default=addr.is_default,
                created_at=addr.created_at,
                updated_at=addr.updated_at,
            )
            for addr in model.shipping_addresses
        ]

        return Customer(
            id=CustomerId(model.id),
            name=CustomerName(model.name),
            email=EmailAddress(model.email),
            member_rank=MemberRank(model.member_rank),
            shipping_addresses=shipping_addresses,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
```

**設計判断:**
- `save()` メソッドで顧客本体と配送先住所を一括保存
- 配送先住所は削除→再作成方式で実装（簡潔性を優先）
- `_to_entity()` でORMモデルをドメインエンティティに変換（Address値オブジェクトも再構築）

#### OrderRepository実装（変更） (`infrastructure/repositories/order_repository.py`)
```python
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session

from app.domain.order.repositories.order_repository import IOrderRepository
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.product.value_objects.product_id import ProductId


class OrderRepository(IOrderRepository):
    """注文リポジトリ実装"""

    def __init__(self, db: Session):
        self.db = db

    def exists_active_order_with_product(self, product_id: ProductId) -> bool:
        """未完了注文に商品が含まれているか確認する（スタブ実装）"""
        # 注文エンドポイント実装時に完成させる
        # 現時点では常にFalseを返す（削除を許可）
        return False

    def find_by_customer_id(
        self,
        customer_id: CustomerId,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[dict], int]:
        """顧客IDで注文一覧を取得する（スタブ実装）"""
        # 注文エンドポイント実装時に完成させる
        # 現時点では空のリストを返す
        return [], 0
```

**設計判断:**
- `find_by_customer_id()` をスタブ実装として追加
- 注文テーブルが未実装のため、空のリストと総件数0を返す
- 注文エンドポイント実装後に実装を完成させる

### 2.3 Alembicマイグレーション

#### マイグレーションファイル (`alembic/versions/YYYYMMDD_create_customers_and_shipping_addresses.py`)
```python
"""create customers and shipping_addresses tables

Revision ID: xxxxxxxxxx
Revises: (previous_revision)
Create Date: 2026-02-04 XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'xxxxxxxxxx'
down_revision = '(previous_revision)'
branch_labels = None
depends_on = None


def upgrade():
    # customersテーブル作成
    op.create_table(
        'customers',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('member_rank', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.CheckConstraint(
            "member_rank IN ('BRONZE', 'SILVER', 'GOLD')",
            name='check_member_rank'
        )
    )
    op.create_index('idx_customers_email', 'customers', ['email'])

    # shipping_addressesテーブル作成
    op.create_table(
        'shipping_addresses',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('customer_id', sa.String(36), nullable=False),
        sa.Column('label', sa.String(50), nullable=False),
        sa.Column('postal_code', sa.String(10), nullable=False),
        sa.Column('prefecture', sa.String(10), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('street', sa.String(200), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], )
    )
    op.create_index('idx_shipping_addresses_customer_id', 'shipping_addresses', ['customer_id'])


def downgrade():
    op.drop_index('idx_shipping_addresses_customer_id', table_name='shipping_addresses')
    op.drop_table('shipping_addresses')
    op.drop_index('idx_customers_email', table_name='customers')
    op.drop_table('customers')
```

**設計判断:**
- 外部キー制約を追加（Customer → ShippingAddress）
- `downgrade()` でロールバック可能にする

---

## 3. Application層（アプリケーション層）

### 3.1 DTO（Data Transfer Object）

#### CustomerDTO (`application/customer/dtos/customer_dto.py`)
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ShippingAddressDTO:
    """配送先住所DTO"""
    address_id: str
    label: str
    postal_code: str
    prefecture: str
    city: str
    street: str
    is_default: bool


@dataclass
class CustomerDTO:
    """顧客DTO（UseCase層の入出力）"""
    customer_id: str
    name: str
    email: str
    member_rank: str
    shipping_addresses: list[ShippingAddressDTO]
    created_at: datetime


@dataclass
class RegisterCustomerInputDTO:
    """顧客登録入力DTO"""
    name: str
    email: str
    shipping_address: dict  # label, postal_code, prefecture, city, street


@dataclass
class UpdateCustomerInputDTO:
    """顧客更新入力DTO"""
    name: str
    email: str


@dataclass
class AddShippingAddressInputDTO:
    """配送先住所追加入力DTO"""
    label: str
    postal_code: str
    prefecture: str
    city: str
    street: str
    is_default: bool
```

#### OrderDTO (`application/customer/dtos/order_dto.py`)
```python
from dataclasses import dataclass
from datetime import datetime


@dataclass
class OrderSummaryDTO:
    """注文サマリーDTO（顧客注文履歴用）"""
    order_id: str
    status: str
    total_amount: int
    item_count: int
    ordered_at: datetime


@dataclass
class PaginationDTO:
    """ページネーションDTO"""
    total: int
    page: int
    per_page: int
```

**設計判断:**
- DTOはプリミティブ型のみで構成（値オブジェクトを使わない）
- UseCase層とPresentation層の境界でデータ構造を変換

### 3.2 UseCase

#### GetCustomerUseCase (`application/customer/usecases/get_customer_usecase.py`)
```python
from app.domain.customer.repositories.customer_repository import ICustomerRepository
from app.domain.customer.value_objects.customer_id import CustomerId
from app.application.customer.dtos.customer_dto import CustomerDTO, ShippingAddressDTO
from app.application.customer.exceptions import CustomerNotFoundError


class GetCustomerUseCase:
    """顧客情報取得ユースケース"""

    def __init__(self, customer_repository: ICustomerRepository):
        self.customer_repository = customer_repository

    def execute(self, customer_id: str) -> CustomerDTO:
        """顧客情報を取得する"""
        customer = self.customer_repository.find_by_id(CustomerId(customer_id))
        if customer is None:
            raise CustomerNotFoundError(f"Customer with ID '{customer_id}' not found")

        # DTOに変換
        shipping_addresses = [
            ShippingAddressDTO(
                address_id=addr.id,
                label=addr.label,
                postal_code=addr.address.postal_code,
                prefecture=addr.address.prefecture,
                city=addr.address.city,
                street=addr.address.street,
                is_default=addr.is_default,
            )
            for addr in customer.shipping_addresses
        ]

        return CustomerDTO(
            customer_id=customer.id.value,
            name=customer.name.value,
            email=customer.email.value,
            member_rank=customer.member_rank.value,
            shipping_addresses=shipping_addresses,
            created_at=customer.created_at,
        )
```

#### RegisterCustomerUseCase (`application/customer/usecases/register_customer_usecase.py`)
```python
from sqlalchemy.orm import Session

from app.domain.customer.entities.customer import Customer
from app.domain.customer.entities.shipping_address import ShippingAddress
from app.domain.customer.repositories.customer_repository import ICustomerRepository
from app.domain.customer.value_objects.customer_name import CustomerName
from app.domain.customer.value_objects.email_address import EmailAddress
from app.domain.customer.value_objects.address import Address
from app.application.customer.dtos.customer_dto import RegisterCustomerInputDTO, CustomerDTO, ShippingAddressDTO
from app.application.customer.exceptions import DuplicateEmailError


class RegisterCustomerUseCase:
    """顧客登録ユースケース"""

    def __init__(
        self,
        customer_repository: ICustomerRepository,
        db: Session,
    ):
        self.customer_repository = customer_repository
        self.db = db

    def execute(self, input_dto: RegisterCustomerInputDTO) -> CustomerDTO:
        """顧客を登録する"""
        # メールアドレス重複チェック
        existing_customer = self.customer_repository.find_by_email(
            EmailAddress(input_dto.email)
        )
        if existing_customer is not None:
            raise DuplicateEmailError(f"Email '{input_dto.email}' already exists")

        # ドメインオブジェクト生成
        customer = Customer.create(
            name=CustomerName(input_dto.name),
            email=EmailAddress(input_dto.email),
        )

        # 初期配送先住所を追加
        initial_address = ShippingAddress.create(
            label=input_dto.shipping_address["label"],
            address=Address(
                postal_code=input_dto.shipping_address["postal_code"],
                prefecture=input_dto.shipping_address["prefecture"],
                city=input_dto.shipping_address["city"],
                street=input_dto.shipping_address["street"],
            ),
            is_default=True,  # 初期住所は必ずデフォルト
        )
        customer.add_shipping_address(initial_address)

        # トランザクション内で永続化
        try:
            self.customer_repository.save(customer)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

        # DTOに変換して返却
        shipping_addresses = [
            ShippingAddressDTO(
                address_id=addr.id,
                label=addr.label,
                postal_code=addr.address.postal_code,
                prefecture=addr.address.prefecture,
                city=addr.address.city,
                street=addr.address.street,
                is_default=addr.is_default,
            )
            for addr in customer.shipping_addresses
        ]

        return CustomerDTO(
            customer_id=customer.id.value,
            name=customer.name.value,
            email=customer.email.value,
            member_rank=customer.member_rank.value,
            shipping_addresses=shipping_addresses,
            created_at=customer.created_at,
        )
```

**設計判断:**
- トランザクション制御をApplication層で実施
- メールアドレス重複チェックはApplication層の責務
- 初期配送先住所は必ずデフォルト（`is_default=True`）

#### UpdateCustomerUseCase (`application/customer/usecases/update_customer_usecase.py`)
```python
from sqlalchemy.orm import Session

from app.domain.customer.repositories.customer_repository import ICustomerRepository
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.customer.value_objects.customer_name import CustomerName
from app.domain.customer.value_objects.email_address import EmailAddress
from app.application.customer.dtos.customer_dto import UpdateCustomerInputDTO, CustomerDTO, ShippingAddressDTO
from app.application.customer.exceptions import CustomerNotFoundError, DuplicateEmailError


class UpdateCustomerUseCase:
    """顧客情報更新ユースケース"""

    def __init__(self, customer_repository: ICustomerRepository, db: Session):
        self.customer_repository = customer_repository
        self.db = db

    def execute(self, customer_id: str, input_dto: UpdateCustomerInputDTO) -> CustomerDTO:
        """顧客情報を更新する"""
        # 顧客を取得
        customer = self.customer_repository.find_by_id(CustomerId(customer_id))
        if customer is None:
            raise CustomerNotFoundError(f"Customer with ID '{customer_id}' not found")

        # メールアドレス変更時は重複チェック
        new_email = EmailAddress(input_dto.email)
        if new_email.value != customer.email.value:
            existing = self.customer_repository.find_by_email(new_email)
            if existing is not None and existing.id.value != customer_id:
                raise DuplicateEmailError(f"Email '{input_dto.email}' already exists")

        # ドメインオブジェクトを更新
        customer.update(
            name=CustomerName(input_dto.name),
            email=new_email,
        )

        # 永続化
        try:
            self.customer_repository.save(customer)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

        # DTOに変換して返却
        shipping_addresses = [
            ShippingAddressDTO(
                address_id=addr.id,
                label=addr.label,
                postal_code=addr.address.postal_code,
                prefecture=addr.address.prefecture,
                city=addr.address.city,
                street=addr.address.street,
                is_default=addr.is_default,
            )
            for addr in customer.shipping_addresses
        ]

        return CustomerDTO(
            customer_id=customer.id.value,
            name=customer.name.value,
            email=customer.email.value,
            member_rank=customer.member_rank.value,
            shipping_addresses=shipping_addresses,
            created_at=customer.created_at,
        )
```

**設計判断:**
- メールアドレス変更時の重複チェックを実施
- 自分自身のメールアドレスとの重複は許可（IDで判定）

#### AddShippingAddressUseCase (`application/customer/usecases/add_shipping_address_usecase.py`)
```python
from sqlalchemy.orm import Session

from app.domain.customer.repositories.customer_repository import ICustomerRepository
from app.domain.customer.entities.shipping_address import ShippingAddress
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.customer.value_objects.address import Address
from app.application.customer.dtos.customer_dto import AddShippingAddressInputDTO, ShippingAddressDTO
from app.application.customer.exceptions import CustomerNotFoundError


class AddShippingAddressUseCase:
    """配送先住所追加ユースケース"""

    def __init__(self, customer_repository: ICustomerRepository, db: Session):
        self.customer_repository = customer_repository
        self.db = db

    def execute(
        self, customer_id: str, input_dto: AddShippingAddressInputDTO
    ) -> ShippingAddressDTO:
        """配送先住所を追加する"""
        # 顧客を取得
        customer = self.customer_repository.find_by_id(CustomerId(customer_id))
        if customer is None:
            raise CustomerNotFoundError(f"Customer with ID '{customer_id}' not found")

        # 配送先住所を生成
        new_address = ShippingAddress.create(
            label=input_dto.label,
            address=Address(
                postal_code=input_dto.postal_code,
                prefecture=input_dto.prefecture,
                city=input_dto.city,
                street=input_dto.street,
            ),
            is_default=input_dto.is_default,
        )

        # 顧客に追加（ドメインルールで最大5件チェック、デフォルト管理）
        customer.add_shipping_address(new_address)

        # 永続化
        try:
            self.customer_repository.save(customer)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

        # DTOに変換して返却
        return ShippingAddressDTO(
            address_id=new_address.id,
            label=new_address.label,
            postal_code=new_address.address.postal_code,
            prefecture=new_address.address.prefecture,
            city=new_address.address.city,
            street=new_address.address.street,
            is_default=new_address.is_default,
        )
```

**設計判断:**
- 配送先住所の追加はドメイン層（`Customer.add_shipping_address()`）で制御
- 最大5件制約とデフォルト管理はドメイン層が担保

#### ListCustomerOrdersUseCase (`application/customer/usecases/list_customer_orders_usecase.py`)
```python
from typing import Optional, Tuple, List

from app.domain.customer.repositories.customer_repository import ICustomerRepository
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.order.repositories.order_repository import IOrderRepository
from app.application.customer.dtos.order_dto import OrderSummaryDTO, PaginationDTO
from app.application.customer.exceptions import CustomerNotFoundError


class ListCustomerOrdersUseCase:
    """顧客注文履歴取得ユースケース（スタブ実装）"""

    def __init__(
        self,
        customer_repository: ICustomerRepository,
        order_repository: IOrderRepository,
    ):
        self.customer_repository = customer_repository
        self.order_repository = order_repository

    def execute(
        self,
        customer_id: str,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[OrderSummaryDTO], PaginationDTO]:
        """顧客の注文履歴を取得する（スタブ実装）"""
        # 顧客の存在確認
        customer = self.customer_repository.find_by_id(CustomerId(customer_id))
        if customer is None:
            raise CustomerNotFoundError(f"Customer with ID '{customer_id}' not found")

        # 注文一覧を取得（スタブ実装なので空のリストが返る）
        orders, total = self.order_repository.find_by_customer_id(
            CustomerId(customer_id), status, page, per_page
        )

        # DTOに変換（スタブ実装なので空のリスト）
        order_dtos = []

        pagination = PaginationDTO(total=total, page=page, per_page=per_page)

        return order_dtos, pagination
```

**設計判断:**
- 顧客の存在確認を実施
- スタブ実装として空のリストを返す
- 注文エンドポイント実装後に完全な実装に置き換える

### 3.3 Application層例外

#### exceptions.py (`application/customer/exceptions.py`)
```python
class CustomerApplicationError(Exception):
    """顧客Application層例外の基底クラス"""
    pass


class CustomerNotFoundError(CustomerApplicationError):
    """顧客が見つからないエラー"""
    pass


class DuplicateEmailError(CustomerApplicationError):
    """メールアドレス重複エラー"""
    pass
```

---

## 4. Presentation層（プレゼンテーション層）

### 4.1 Pydanticスキーマ

#### customer.py (`schemas/customer.py`)
```python
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class ShippingAddressRequest(BaseModel):
    """配送先住所リクエスト"""
    label: str = Field(..., min_length=1, max_length=50)
    postal_code: str = Field(..., pattern=r"^\d{3}-\d{4}$")
    prefecture: str = Field(..., min_length=1, max_length=10)
    city: str = Field(..., min_length=1, max_length=100)
    street: str = Field(..., min_length=1, max_length=200)


class CustomerRegisterRequest(BaseModel):
    """顧客登録リクエスト"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    shipping_address: ShippingAddressRequest


class CustomerUpdateRequest(BaseModel):
    """顧客更新リクエスト"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr


class ShippingAddressAddRequest(BaseModel):
    """配送先住所追加リクエスト"""
    label: str = Field(..., min_length=1, max_length=50)
    postal_code: str = Field(..., pattern=r"^\d{3}-\d{4}$")
    prefecture: str = Field(..., min_length=1, max_length=10)
    city: str = Field(..., min_length=1, max_length=100)
    street: str = Field(..., min_length=1, max_length=200)
    is_default: bool = False


class ShippingAddressResponse(BaseModel):
    """配送先住所レスポンス"""
    address_id: str
    label: str
    postal_code: str
    prefecture: str
    city: str
    street: str
    is_default: bool


class CustomerResponse(BaseModel):
    """顧客レスポンス"""
    customer_id: str
    name: str
    email: str
    member_rank: str
    shipping_addresses: list[ShippingAddressResponse]
    created_at: datetime


class OrderSummaryResponse(BaseModel):
    """注文サマリーレスポンス"""
    order_id: str
    status: str
    total_amount: int
    item_count: int
    ordered_at: datetime


class PaginationResponse(BaseModel):
    """ページネーションレスポンス"""
    total: int
    page: int
    per_page: int


class CustomerOrderListResponse(BaseModel):
    """顧客注文履歴レスポンス"""
    data: list[OrderSummaryResponse]
    pagination: PaginationResponse
```

**設計判断:**
- Pydantic v2の `Field` でバリデーション定義
- `EmailStr` でメールアドレスフォーマットを検証
- 郵便番号は正規表現パターンで検証（`^\d{3}-\d{4}$`）

### 4.2 FastAPIルーター

#### customers.py (`api/v1/endpoints/customers.py`)
```python
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.customer import (
    CustomerRegisterRequest,
    CustomerUpdateRequest,
    ShippingAddressAddRequest,
    CustomerResponse,
    ShippingAddressResponse,
    CustomerOrderListResponse,
    OrderSummaryResponse,
    PaginationResponse,
)
from app.application.customer.usecases.get_customer_usecase import GetCustomerUseCase
from app.application.customer.usecases.register_customer_usecase import RegisterCustomerUseCase
from app.application.customer.usecases.update_customer_usecase import UpdateCustomerUseCase
from app.application.customer.usecases.add_shipping_address_usecase import AddShippingAddressUseCase
from app.application.customer.usecases.list_customer_orders_usecase import ListCustomerOrdersUseCase
from app.application.customer.dtos.customer_dto import (
    RegisterCustomerInputDTO,
    UpdateCustomerInputDTO,
    AddShippingAddressInputDTO,
)
from app.application.customer.exceptions import (
    CustomerNotFoundError,
    DuplicateEmailError,
)
from app.infrastructure.repositories.customer_repository import CustomerRepository
from app.infrastructure.repositories.order_repository import OrderRepository


router = APIRouter()


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
):
    """顧客情報取得"""
    customer_repository = CustomerRepository(db)
    usecase = GetCustomerUseCase(customer_repository)

    try:
        customer_dto = usecase.execute(customer_id)
        return CustomerResponse(**customer_dto.__dict__)
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
        customer_dto = usecase.execute(input_dto)
        return CustomerResponse(**customer_dto.__dict__)
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
        customer_dto = usecase.execute(customer_id, input_dto)
        return CustomerResponse(**customer_dto.__dict__)
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
        return ShippingAddressResponse(**address_dto.__dict__)
    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        # 最大5件超過エラーもValueErrorとして扱う
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{customer_id}/orders", response_model=CustomerOrderListResponse)
def list_customer_orders(
    customer_id: str,
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """顧客注文履歴取得（スタブ実装）"""
    customer_repository = CustomerRepository(db)
    order_repository = OrderRepository(db)
    usecase = ListCustomerOrdersUseCase(customer_repository, order_repository)

    try:
        order_dtos, pagination_dto = usecase.execute(customer_id, status, page, per_page)

        return CustomerOrderListResponse(
            data=[OrderSummaryResponse(**dto.__dict__) for dto in order_dtos],
            pagination=PaginationResponse(**pagination_dto.__dict__),
        )
    except CustomerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
```

**設計判断:**
- 各エンドポイントでリポジトリとUseCaseを組み立てる（DI）
- Application層の例外をHTTPステータスコードにマッピング
- `Query` でクエリパラメータのバリデーション

### 4.3 ルーター登録

#### router.py（変更） (`api/v1/router.py`)
```python
from fastapi import APIRouter
from app.api.v1.endpoints import health, examples, products, customers  # customersを追加

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(examples.router, prefix="/examples", tags=["examples"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])  # 追加
```

---

## 変更するコンポーネント

### 新規作成ファイル
- Domain層: 12ファイル（エンティティ、値オブジェクト、リポジトリIF、例外）
- Application層: 11ファイル（DTO、UseCase、例外）
- Infrastructure層: 1ファイル（Customerリポジトリ実装）
- Presentation層: 2ファイル（スキーマ、ルーター）
- Alembicマイグレーション: 1ファイル
- テスト: 10ファイル

### 既存ファイルへの変更
- `backend/app/infrastructure/database/models.py` — `CustomerModel` と `ShippingAddressModel` を追加
- `backend/app/infrastructure/repositories/order_repository.py` — `find_by_customer_id()` メソッド追加（スタブ）
- `backend/app/domain/order/repositories/order_repository.py` — `find_by_customer_id()` メソッド追加（インターフェース）
- `backend/app/api/v1/router.py` — `/customers` ルーターを登録

---

## テスト戦略

### 1. Domain層テスト（単体テスト）

#### 目標カバレッジ: 80%以上

**テスト対象:**
- 値オブジェクトのバリデーション（EmailAddress、Address等）
- Customerエンティティのファクトリメソッド
- Customerエンティティのコマンドメソッド（add_shipping_address、update等）
- 配送先住所の最大5件制約
- デフォルト住所の一意性

**テスト例:**
```python
# tests/unit/domain/customer/test_customer_entity.py

def test_create_customer():
    """顧客を生成できる"""
    customer = Customer.create(
        name=CustomerName("田中太郎"),
        email=EmailAddress("tanaka@example.com"),
    )

    assert customer.id is not None
    assert customer.name.value == "田中太郎"
    assert customer.email.value == "tanaka@example.com"
    assert customer.member_rank == MemberRank.BRONZE
    assert len(customer.shipping_addresses) == 0


def test_add_shipping_address_exceeds_limit():
    """配送先住所が5件を超えるとエラー"""
    customer = Customer.create(
        name=CustomerName("田中太郎"),
        email=EmailAddress("tanaka@example.com"),
    )

    # 5件追加
    for i in range(5):
        address = ShippingAddress.create(
            label=f"住所{i+1}",
            address=Address("100-0001", "東京都", "千代田区", f"千代田{i+1}-1-1"),
            is_default=False,
        )
        customer.add_shipping_address(address)

    # 6件目の追加は失敗
    with pytest.raises(ValueError, match="Cannot add more than 5 shipping addresses"):
        address6 = ShippingAddress.create(
            label="住所6",
            address=Address("100-0001", "東京都", "千代田区", "千代田6-1-1"),
            is_default=False,
        )
        customer.add_shipping_address(address6)


def test_add_default_address_unsets_previous_default():
    """デフォルト住所を追加すると既存のデフォルトが解除される"""
    customer = Customer.create(
        name=CustomerName("田中太郎"),
        email=EmailAddress("tanaka@example.com"),
    )

    addr1 = ShippingAddress.create(
        label="自宅",
        address=Address("100-0001", "東京都", "千代田区", "千代田1-1-1"),
        is_default=True,
    )
    customer.add_shipping_address(addr1)

    addr2 = ShippingAddress.create(
        label="会社",
        address=Address("150-0001", "東京都", "渋谷区", "渋谷2-2-2"),
        is_default=True,
    )
    customer.add_shipping_address(addr2)

    # 1件目はデフォルトが解除される
    assert not customer.shipping_addresses[0].is_default
    # 2件目がデフォルト
    assert customer.shipping_addresses[1].is_default
```

### 2. Application層テスト（単体テスト）

#### 目標カバレッジ: 80%以上

**テスト対象:**
- UseCaseの正常系
- UseCaseのエラーケース（メールアドレス重複、顧客未存在、配送先住所上限超過等）
- トランザクション境界

**テスト例:**
```python
# tests/unit/application/customer/test_register_customer_usecase.py

def test_register_customer_success(mock_customer_repository, mock_db):
    """顧客登録が成功する"""
    mock_customer_repository.find_by_email.return_value = None

    usecase = RegisterCustomerUseCase(mock_customer_repository, mock_db)

    input_dto = RegisterCustomerInputDTO(
        name="田中太郎",
        email="tanaka@example.com",
        shipping_address={
            "label": "自宅",
            "postal_code": "100-0001",
            "prefecture": "東京都",
            "city": "千代田区",
            "street": "千代田1-1-1",
        },
    )

    result = usecase.execute(input_dto)

    assert result.name == "田中太郎"
    assert result.email == "tanaka@example.com"
    assert result.member_rank == "BRONZE"
    assert len(result.shipping_addresses) == 1
    assert result.shipping_addresses[0].is_default is True
    mock_customer_repository.save.assert_called_once()
    mock_db.commit.assert_called_once()


def test_register_customer_with_duplicate_email_raises_error(mock_customer_repository, mock_db):
    """メールアドレス重複時はエラーを返す"""
    existing_customer = Customer.create(
        name=CustomerName("既存顧客"),
        email=EmailAddress("tanaka@example.com"),
    )
    mock_customer_repository.find_by_email.return_value = existing_customer

    usecase = RegisterCustomerUseCase(mock_customer_repository, mock_db)

    input_dto = RegisterCustomerInputDTO(
        name="新規顧客",
        email="tanaka@example.com",
        shipping_address={
            "label": "自宅",
            "postal_code": "100-0001",
            "prefecture": "東京都",
            "city": "千代田区",
            "street": "千代田1-1-1",
        },
    )

    with pytest.raises(DuplicateEmailError):
        usecase.execute(input_dto)
```

### 3. Integration層テスト（統合テスト）

#### 目標カバレッジ: 主要なエンドポイントをカバー

**テスト対象:**
- APIエンドポイントの正常系
- HTTPステータスコード
- レスポンス構造
- エラーレスポンス

---

## 実装上の注意点（商品エンドポイントとの違い）

### 1. 集約内エンティティの管理
- **商品エンドポイント**: 商品と在庫は独立した集約（それぞれリポジトリを持つ）
- **顧客エンドポイント**: ShippingAddressは集約内エンティティ（独自リポジトリなし、Customer経由でアクセス）

### 2. 論理削除の扱い
- **商品エンドポイント**: 論理削除を実装（`deleted_at`）
- **顧客エンドポイント**: 論理削除は実装しない（顧客は削除しない方針）

### 3. リレーションの扱い
- **商品エンドポイント**: Product-Stock間に外部キー制約なし（集約の独立性）
- **顧客エンドポイント**: Customer-ShippingAddress間に外部キー制約あり（集約内の整合性保証）

### 4. Eager Loadingの活用
- **商品エンドポイント**: Productのみ取得（Stockは別途取得）
- **顧客エンドポイント**: Customerと一緒にShippingAddressもEager Loadingで取得（N+1問題回避）

### 5. ドメインルールの複雑性
- **商品エンドポイント**: SKU一意性、価格の非負
- **顧客エンドポイント**: メールアドレス一意性、配送先住所最大5件、デフォルト住所の一意性

### 6. OrderRepositoryの扱い
- **商品エンドポイント**: 商品削除チェック用に `exists_active_order_with_product()` を定義
- **顧客エンドポイント**: 顧客注文履歴取得用に `find_by_customer_id()` を追加（スタブ実装）

---

## まとめ

本設計書では、OrderHub（注文管理システム）の顧客エンドポイントをDDDレイヤードアーキテクチャに基づいて実装する詳細な設計を定義した。

**実装の要点:**
1. **4層アーキテクチャ**: Presentation / Application / Domain / Infrastructure の責務を明確に分離
2. **純粋なドメインモデル**: ドメイン層は外部ライブラリに依存しない
3. **集約内エンティティの適切な管理**: ShippingAddressは独自リポジトリを持たず、Customer経由でのみアクセス
4. **値オブジェクトによるバリデーション**: メールアドレス、郵便番号等のフォーマットをドメイン層で検証
5. **ドメインルールの強制**: 配送先住所最大5件、デフォルト住所の一意性をドメイン層で保証
6. **スタブ実装の明示**: 顧客注文履歴エンドポイントはスタブとして実装

**次のステップ:**
- tasklist.mdの作成
- 実装の開始（Domain層 → Infrastructure層 → Application層 → Presentation層の順）
- 各層のテスト実装
- 統合テストの実施
