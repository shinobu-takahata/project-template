# 設計書: 商品エンドポイント実装

## 概要
OrderHub（注文管理システム）の商品エンドポイントをDDDレイヤードアーキテクチャに基づいて実装する。
既存のFastAPIプロジェクト構造に従い、4つの層（Presentation / Application / Domain / Infrastructure）を明確に分離し、ドメイン駆動設計の原則を遵守する。

## 実装アプローチ

### アーキテクチャ方針
1. **DDDレイヤードアーキテクチャ**: 既存の `backend/app` ディレクトリ構造を活用し、各層の責務を明確に分離する
2. **依存性逆転の原則**: Domain層にリポジトリインターフェースを定義し、Infrastructure層で実装する
3. **純粋なドメインモデル**: Domain層は外部ライブラリ（FastAPI、SQLAlchemy等）に依存しない
4. **トランザクション境界**: Application層（UseCase）でトランザクションを制御する
5. **値オブジェクトによるバリデーション**: コンストラクタで不変条件を検証し、不正な値の生成を防ぐ

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
│   ├── product/                          # 新規: 商品集約
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   └── product.py                # 商品エンティティ（集約ルート）
│   │   ├── value_objects/
│   │   │   ├── __init__.py
│   │   │   ├── product_id.py            # 商品ID
│   │   │   ├── product_name.py          # 商品名
│   │   │   ├── sku.py                   # SKU
│   │   │   └── price.py                 # 価格
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── product_repository.py    # Productリポジトリインターフェース
│   │   │   ├── stock_repository.py      # Stockリポジトリインターフェース（スタブ実装用）
│   │   │   └── order_repository.py      # Orderリポジトリインターフェース（スタブ実装用）
│   │   └── exceptions.py                # 商品ドメイン例外
│   ├── stock/                            # 新規: 在庫集約（初期在庫作成用の最小実装）
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   └── stock.py                 # 在庫エンティティ（集約ルート）
│   │   └── value_objects/
│   │       ├── __init__.py
│   │       ├── stock_id.py              # 在庫ID
│   │       └── stock_quantity.py        # 在庫数量
│   └── shared/                           # 新規: 共通値オブジェクト
│       ├── __init__.py
│       └── value_objects/
│           ├── __init__.py
│           └── quantity.py              # 数量（注文数量と区別）
├── application/
│   └── product/                          # 新規: 商品ユースケース
│       ├── __init__.py
│       ├── dtos/
│       │   ├── __init__.py
│       │   ├── product_dto.py           # 商品DTO（UseCase層の入出力）
│       │   └── pagination_dto.py        # ページネーションDTO
│       ├── usecases/
│       │   ├── __init__.py
│       │   ├── list_products_usecase.py       # GET /api/v1/products
│       │   ├── register_product_usecase.py    # POST /api/v1/products
│       │   ├── update_product_usecase.py      # PUT /api/v1/products/{id}
│       │   └── delete_product_usecase.py      # DELETE /api/v1/products/{id}
│       └── exceptions.py                # Application層例外
├── infrastructure/
│   ├── database/
│   │   └── models.py                    # 変更: 商品・在庫テーブルモデル追加
│   └── repositories/
│       ├── product_repository.py        # 新規: Productリポジトリ実装
│       ├── stock_repository.py          # 新規: Stockリポジトリ実装（スタブ）
│       └── order_repository.py          # 新規: Orderリポジトリ実装（スタブ）
├── api/v1/
│   └── endpoints/
│       └── products.py                  # 新規: 商品エンドポイント
├── schemas/
│   └── product.py                       # 新規: 商品Pydanticスキーマ
└── core/
    └── errors.py                        # 新規: グローバルエラーハンドラ

alembic/
└── versions/
    └── YYYYMMDD_create_products_and_stocks.py  # 新規: マイグレーション

tests/
├── unit/
│   ├── domain/
│   │   ├── product/
│   │   │   ├── test_product_entity.py         # 商品エンティティのテスト
│   │   │   ├── test_product_value_objects.py  # 値オブジェクトのテスト
│   │   │   └── test_stock_entity.py           # 在庫エンティティのテスト
│   │   └── ...
│   ├── application/
│   │   ├── product/
│   │   │   ├── test_list_products_usecase.py
│   │   │   ├── test_register_product_usecase.py
│   │   │   ├── test_update_product_usecase.py
│   │   │   └── test_delete_product_usecase.py
│   │   └── ...
│   └── mocks/
│       ├── mock_product_repository.py
│       ├── mock_stock_repository.py
│       └── mock_order_repository.py
└── integration/
    └── api/
        └── v1/
            └── test_products_endpoint.py        # APIエンドポイントの統合テスト
```

---

## 各層の詳細設計

## 1. Domain層（ドメイン層）

### 1.1 値オブジェクト

#### ProductId (`domain/product/value_objects/product_id.py`)
```python
from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class ProductId:
    """商品ID値オブジェクト"""
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("ProductId cannot be empty")

    @staticmethod
    def generate() -> "ProductId":
        """新しい商品IDを生成する"""
        return ProductId(str(uuid.uuid4()))
```

**設計判断:**
- UUIDをドメイン層で生成（Infrastructure層に依存しない）
- `frozen=True` で不変性を保証
- バリデーションは `__post_init__` で実施

#### ProductName (`domain/product/value_objects/product_name.py`)
```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ProductName:
    """商品名値オブジェクト"""
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("ProductName cannot be empty")
        if len(self.value) > 200:
            raise ValueError("ProductName must be 200 characters or less")
```

#### SKU (`domain/product/value_objects/sku.py`)
```python
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SKU:
    """SKU（在庫管理単位）値オブジェクト"""
    value: str

    PATTERN = re.compile(r"^[A-Za-z0-9\-]+$")

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("SKU cannot be empty")
        if len(self.value) > 50:
            raise ValueError("SKU must be 50 characters or less")
        if not self.PATTERN.match(self.value):
            raise ValueError("SKU must contain only alphanumeric characters and hyphens")
```

**設計判断:**
- パターンマッチングによるフォーマット検証
- ビジネスルール（英数字とハイフンのみ）をドメイン層で表現

#### Price (`domain/product/value_objects/price.py`)
```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Price:
    """価格値オブジェクト（円単位）"""
    value: int

    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Price must be non-negative")
```

**設計判断:**
- 整数型（円単位）で保持し、浮動小数点の誤差を回避
- 0円を許容する（無料商品のケース）

#### StockQuantity (`domain/stock/value_objects/stock_quantity.py`)
```python
from dataclasses import dataclass


@dataclass(frozen=True)
class StockQuantity:
    """在庫数量値オブジェクト"""
    value: int

    def __post_init__(self):
        if self.value < 0:
            raise ValueError("StockQuantity must be non-negative")
```

**設計判断:**
- 在庫数量は0を許容する（在庫切れ状態）

### 1.2 エンティティ

#### Product（集約ルート） (`domain/product/entities/product.py`)
```python
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Optional

from app.domain.product.value_objects.product_id import ProductId
from app.domain.product.value_objects.product_name import ProductName
from app.domain.product.value_objects.sku import SKU
from app.domain.product.value_objects.price import Price


@dataclass
class Product:
    """商品エンティティ（集約ルート）"""
    id: ProductId
    name: ProductName
    sku: SKU
    price: Price
    category: str
    description: Optional[str] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def create(
        name: ProductName,
        sku: SKU,
        price: Price,
        category: str,
        description: Optional[str] = None,
    ) -> "Product":
        """商品を生成する（ファクトリメソッド）"""
        return Product(
            id=ProductId.generate(),
            name=name,
            sku=sku,
            price=price,
            category=category,
            description=description,
            deleted_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def update(
        self,
        name: ProductName,
        price: Price,
        category: str,
        description: Optional[str],
    ) -> None:
        """商品情報を更新する"""
        if self.deleted_at is not None:
            raise ValueError("Cannot update a deleted product")

        self.name = name
        self.price = price
        self.category = category
        self.description = description
        self.updated_at = datetime.now(UTC)

    def delete(self) -> None:
        """論理削除する"""
        if self.deleted_at is not None:
            raise ValueError("Product is already deleted")

        self.deleted_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    @property
    def is_deleted(self) -> bool:
        """削除済みかどうか"""
        return self.deleted_at is not None
```

**設計判断:**
- ファクトリメソッド `create()` で生成ロジックをカプセル化
- 論理削除済み商品の更新を防ぐビジネスルール
- `is_deleted` プロパティで削除状態を判定

#### Stock（集約ルート） (`domain/stock/entities/stock.py`)
```python
from dataclasses import dataclass, field
from datetime import datetime, UTC

from app.domain.stock.value_objects.stock_id import StockId
from app.domain.stock.value_objects.stock_quantity import StockQuantity
from app.domain.product.value_objects.product_id import ProductId


@dataclass
class Stock:
    """在庫エンティティ（集約ルート）"""
    id: StockId
    product_id: ProductId
    quantity: StockQuantity
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @staticmethod
    def initialize(product_id: ProductId, quantity: StockQuantity) -> "Stock":
        """初期在庫を生成する（ファクトリメソッド）"""
        return Stock(
            id=StockId.generate(),
            product_id=product_id,
            quantity=quantity,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
```

**設計判断:**
- 商品登録時の初期在庫作成のための最小実装
- 在庫集約の完全な実装（引当・解放等）は今後の作業で実装する

### 1.3 リポジトリインターフェース

#### ProductRepository (`domain/product/repositories/product_repository.py`)
```python
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple

from app.domain.product.entities.product import Product
from app.domain.product.value_objects.product_id import ProductId
from app.domain.product.value_objects.sku import SKU


class ProductRepository(ABC):
    """商品リポジトリインターフェース"""

    @abstractmethod
    def find_by_id(self, product_id: ProductId) -> Optional[Product]:
        """IDで商品を取得する"""
        pass

    @abstractmethod
    def find_by_sku(self, sku: SKU) -> Optional[Product]:
        """SKUで商品を取得する"""
        pass

    @abstractmethod
    def find_all(
        self,
        category: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Product], int]:
        """商品一覧を取得する（ページネーション対応）

        Returns:
            Tuple[List[Product], int]: (商品リスト, 総件数)
        """
        pass

    @abstractmethod
    def save(self, product: Product) -> None:
        """商品を保存する（作成・更新）"""
        pass
```

**設計判断:**
- ページネーション機能を `find_all()` に組み込む
- 総件数を返却してPresentation層でページネーション情報を構築

#### StockRepository (`domain/stock/repositories/stock_repository.py`)
```python
from abc import ABC, abstractmethod
from typing import Optional

from app.domain.stock.entities.stock import Stock
from app.domain.product.value_objects.product_id import ProductId


class StockRepository(ABC):
    """在庫リポジトリインターフェース"""

    @abstractmethod
    def save(self, stock: Stock) -> None:
        """在庫を保存する"""
        pass

    @abstractmethod
    def find_by_product_id(self, product_id: ProductId) -> Optional[Stock]:
        """商品IDで在庫を取得する（今後の実装で使用）"""
        pass
```

**設計判断:**
- 今回は `save()` のみ実装し、スタブとして定義

#### OrderRepository (`domain/product/repositories/order_repository.py`)
```python
from abc import ABC, abstractmethod

from app.domain.product.value_objects.product_id import ProductId


class OrderRepository(ABC):
    """注文リポジトリインターフェース（商品削除チェック用）"""

    @abstractmethod
    def exists_active_order_with_product(self, product_id: ProductId) -> bool:
        """未完了注文に商品が含まれているか確認する

        未完了注文: CONFIRMED, PAID, PREPARING, SHIPPED
        """
        pass
```

**設計判断:**
- 商品削除時のチェック用にインターフェースのみ定義
- 今回はスタブ実装（常に `False` を返す）として実装
- 注文エンドポイント実装時に完全な実装に置き換える

### 1.4 ドメイン例外

#### exceptions.py (`domain/product/exceptions.py`)
```python
class ProductDomainError(Exception):
    """商品ドメイン例外の基底クラス"""
    pass


class ProductAlreadyDeletedError(ProductDomainError):
    """論理削除済み商品の操作エラー"""
    pass


class InvalidPriceError(ProductDomainError):
    """不正な価格エラー"""
    pass


class InvalidSKUFormatError(ProductDomainError):
    """不正なSKUフォーマットエラー"""
    pass
```

---

## 2. Infrastructure層（インフラストラクチャ層）

### 2.1 SQLAlchemyモデル

#### models.py（変更） (`infrastructure/database/models.py`)
```python
# 既存のExampleModelに追加

from sqlalchemy import Column, String, Integer, Text, DateTime, CheckConstraint, Index
from datetime import UTC, datetime


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    sku = Column(String(50), nullable=False, unique=True, index=True)
    price = Column(Integer, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("price >= 0", name="check_price_non_negative"),
        Index("idx_products_category", "category"),
        Index("idx_products_deleted_at", "deleted_at"),
    )


class StockModel(Base):
    __tablename__ = "stocks"

    id = Column(String(36), primary_key=True)
    product_id = Column(String(36), nullable=False, unique=True, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="check_quantity_non_negative"),
    )
```

**設計判断:**
- IDは文字列型（UUID）で保存
- `deleted_at` にインデックスを追加（論理削除フィルタのパフォーマンス向上）
- CHECK制約でデータベースレベルの整合性を保証（最終防衛線）

### 2.2 リポジトリ実装

#### ProductRepository実装 (`infrastructure/repositories/product_repository.py`)
```python
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.domain.product.entities.product import Product
from app.domain.product.repositories.product_repository import ProductRepository
from app.domain.product.value_objects.product_id import ProductId
from app.domain.product.value_objects.product_name import ProductName
from app.domain.product.value_objects.sku import SKU
from app.domain.product.value_objects.price import Price
from app.infrastructure.database.models import ProductModel


class ProductRepositoryImpl(ProductRepository):
    """商品リポジトリ実装"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, product_id: ProductId) -> Optional[Product]:
        """IDで商品を取得する"""
        model = self.db.query(ProductModel).filter(
            ProductModel.id == product_id.value,
            ProductModel.deleted_at.is_(None)
        ).first()

        if model is None:
            return None

        return self._to_entity(model)

    def find_by_sku(self, sku: SKU) -> Optional[Product]:
        """SKUで商品を取得する"""
        model = self.db.query(ProductModel).filter(
            ProductModel.sku == sku.value,
            ProductModel.deleted_at.is_(None)
        ).first()

        if model is None:
            return None

        return self._to_entity(model)

    def find_all(
        self,
        category: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Product], int]:
        """商品一覧を取得する"""
        query = self.db.query(ProductModel).filter(ProductModel.deleted_at.is_(None))

        # カテゴリフィルタ
        if category:
            query = query.filter(ProductModel.category == category)

        # 総件数を取得
        total = query.count()

        # ページネーション
        offset = (page - 1) * per_page
        models = query.offset(offset).limit(per_page).all()

        products = [self._to_entity(m) for m in models]
        return products, total

    def save(self, product: Product) -> None:
        """商品を保存する"""
        model = self.db.query(ProductModel).filter(
            ProductModel.id == product.id.value
        ).first()

        if model is None:
            # 新規作成
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
            # 更新
            model.name = product.name.value
            model.price = product.price.value
            model.category = product.category
            model.description = product.description
            model.deleted_at = product.deleted_at
            model.updated_at = product.updated_at

        self.db.flush()

    def _to_entity(self, model: ProductModel) -> Product:
        """モデルをエンティティに変換する"""
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
```

**設計判断:**
- `save()` メソッドで作成・更新を判定（既存レコードの有無で判断）
- `deleted_at.is_(None)` で論理削除フィルタを適用
- `_to_entity()` でORMモデルをドメインエンティティに変換

#### StockRepository実装 (`infrastructure/repositories/stock_repository.py`)
```python
from typing import Optional
from sqlalchemy.orm import Session

from app.domain.stock.entities.stock import Stock
from app.domain.stock.repositories.stock_repository import StockRepository
from app.domain.stock.value_objects.stock_id import StockId
from app.domain.stock.value_objects.stock_quantity import StockQuantity
from app.domain.product.value_objects.product_id import ProductId
from app.infrastructure.database.models import StockModel


class StockRepositoryImpl(StockRepository):
    """在庫リポジトリ実装（初期在庫作成用の最小実装）"""

    def __init__(self, db: Session):
        self.db = db

    def save(self, stock: Stock) -> None:
        """在庫を保存する"""
        model = StockModel(
            id=stock.id.value,
            product_id=stock.product_id.value,
            quantity=stock.quantity.value,
            created_at=stock.created_at,
            updated_at=stock.updated_at,
        )
        self.db.add(model)
        self.db.flush()

    def find_by_product_id(self, product_id: ProductId) -> Optional[Stock]:
        """商品IDで在庫を取得する（スタブ実装）"""
        # 今後の実装で完成させる
        raise NotImplementedError("This method is not implemented yet")
```

**設計判断:**
- 今回は初期在庫作成のみの実装
- `find_by_product_id()` は今後の実装時に完成させる

#### OrderRepository実装 (`infrastructure/repositories/order_repository.py`)
```python
from sqlalchemy.orm import Session

from app.domain.product.repositories.order_repository import OrderRepository
from app.domain.product.value_objects.product_id import ProductId


class OrderRepositoryImpl(OrderRepository):
    """注文リポジトリ実装（スタブ）"""

    def __init__(self, db: Session):
        self.db = db

    def exists_active_order_with_product(self, product_id: ProductId) -> bool:
        """未完了注文に商品が含まれているか確認する（スタブ実装）"""
        # 注文エンドポイント実装時に完成させる
        # 現時点では常にFalseを返す（削除を許可）
        return False
```

**設計判断:**
- 注文テーブルが未実装のため、スタブとして常に `False` を返す
- 注文エンドポイント実装後に実装を完成させる

### 2.3 Alembicマイグレーション

#### マイグレーションファイル (`alembic/versions/YYYYMMDD_create_products_and_stocks.py`)
```python
"""create products and stocks tables

Revision ID: xxxxxxxxxx
Revises:
Create Date: 2026-02-03 XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'xxxxxxxxxx'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # productsテーブル作成
    op.create_table(
        'products',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('sku', sa.String(50), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sku'),
        sa.CheckConstraint('price >= 0', name='check_price_non_negative')
    )
    op.create_index('idx_products_sku', 'products', ['sku'])
    op.create_index('idx_products_category', 'products', ['category'])
    op.create_index('idx_products_deleted_at', 'products', ['deleted_at'])

    # stocksテーブル作成
    op.create_table(
        'stocks',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('product_id', sa.String(36), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id'),
        sa.CheckConstraint('quantity >= 0', name='check_quantity_non_negative')
    )
    op.create_index('idx_stocks_product_id', 'stocks', ['product_id'])


def downgrade():
    op.drop_index('idx_stocks_product_id', table_name='stocks')
    op.drop_table('stocks')
    op.drop_index('idx_products_deleted_at', table_name='products')
    op.drop_index('idx_products_category', table_name='products')
    op.drop_index('idx_products_sku', table_name='products')
    op.drop_table('products')
```

**設計判断:**
- 外部キー制約は追加しない（集約間の独立性を保つ）
- `downgrade()` でロールバック可能にする

---

## 3. Application層（アプリケーション層）

### 3.1 DTO（Data Transfer Object）

#### ProductDTO (`application/product/dtos/product_dto.py`)
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ProductDTO:
    """商品DTO（UseCase層の入出力）"""
    id: str
    name: str
    sku: str
    price: int
    category: str
    description: Optional[str]
    stock_quantity: int
    created_at: datetime
    updated_at: datetime


@dataclass
class RegisterProductInputDTO:
    """商品登録入力DTO"""
    name: str
    sku: str
    price: int
    category: str
    description: Optional[str]
    initial_stock: int


@dataclass
class UpdateProductInputDTO:
    """商品更新入力DTO"""
    name: str
    price: int
    category: str
    description: Optional[str]


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

#### ListProductsUseCase (`application/product/usecases/list_products_usecase.py`)
```python
from typing import List, Tuple, Optional

from app.domain.product.repositories.product_repository import ProductRepository
from app.application.product.dtos.product_dto import ProductDTO, PaginationDTO


class ListProductsUseCase:
    """商品一覧取得ユースケース"""

    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    def execute(
        self,
        category: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[ProductDTO], PaginationDTO]:
        """商品一覧を取得する"""
        # バリデーション
        if page < 1:
            raise ValueError("Page must be greater than 0")
        if per_page < 1 or per_page > 100:
            raise ValueError("Per page must be between 1 and 100")

        # リポジトリから取得
        products, total = self.product_repository.find_all(category, page, per_page)

        # DTOに変換
        product_dtos = [
            ProductDTO(
                id=p.id.value,
                name=p.name.value,
                sku=p.sku.value,
                price=p.price.value,
                category=p.category,
                description=p.description,
                stock_quantity=0,  # 今後の実装で在庫情報を取得
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in products
        ]

        pagination = PaginationDTO(total=total, page=page, per_page=per_page)

        return product_dtos, pagination
```

**設計判断:**
- ページネーションパラメータのバリデーション
- `stock_quantity` は今回は固定値（今後の実装で在庫リポジトリから取得）

#### RegisterProductUseCase (`application/product/usecases/register_product_usecase.py`)
```python
from sqlalchemy.orm import Session

from app.domain.product.entities.product import Product
from app.domain.product.repositories.product_repository import ProductRepository
from app.domain.stock.entities.stock import Stock
from app.domain.stock.repositories.stock_repository import StockRepository
from app.domain.product.value_objects.product_name import ProductName
from app.domain.product.value_objects.sku import SKU
from app.domain.product.value_objects.price import Price
from app.domain.stock.value_objects.stock_quantity import StockQuantity
from app.application.product.dtos.product_dto import RegisterProductInputDTO, ProductDTO
from app.application.product.exceptions import DuplicateSKUError


class RegisterProductUseCase:
    """商品登録ユースケース"""

    def __init__(
        self,
        product_repository: ProductRepository,
        stock_repository: StockRepository,
        db: Session,
    ):
        self.product_repository = product_repository
        self.stock_repository = stock_repository
        self.db = db

    def execute(self, input_dto: RegisterProductInputDTO) -> ProductDTO:
        """商品を登録する"""
        # SKU重複チェック
        existing_product = self.product_repository.find_by_sku(SKU(input_dto.sku))
        if existing_product is not None:
            raise DuplicateSKUError(f"SKU '{input_dto.sku}' already exists")

        # ドメインオブジェクト生成
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

        # トランザクション内で永続化
        try:
            self.product_repository.save(product)
            self.stock_repository.save(stock)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

        # DTOに変換して返却
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
```

**設計判断:**
- トランザクション制御をApplication層で実施
- SKU重複チェックはApplication層の責務（ドメイン層ではリポジトリにアクセスできない）
- 商品と在庫を同一トランザクションで作成

#### UpdateProductUseCase (`application/product/usecases/update_product_usecase.py`)
```python
from sqlalchemy.orm import Session

from app.domain.product.repositories.product_repository import ProductRepository
from app.domain.product.value_objects.product_id import ProductId
from app.domain.product.value_objects.product_name import ProductName
from app.domain.product.value_objects.price import Price
from app.application.product.dtos.product_dto import UpdateProductInputDTO, ProductDTO
from app.application.product.exceptions import ProductNotFoundError


class UpdateProductUseCase:
    """商品更新ユースケース"""

    def __init__(self, product_repository: ProductRepository, db: Session):
        self.product_repository = product_repository
        self.db = db

    def execute(self, product_id: str, input_dto: UpdateProductInputDTO) -> ProductDTO:
        """商品を更新する"""
        # 商品を取得
        product = self.product_repository.find_by_id(ProductId(product_id))
        if product is None:
            raise ProductNotFoundError(f"Product with ID '{product_id}' not found")

        # ドメインオブジェクトを更新
        product.update(
            name=ProductName(input_dto.name),
            price=Price(input_dto.price),
            category=input_dto.category,
            description=input_dto.description,
        )

        # 永続化
        try:
            self.product_repository.save(product)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

        # DTOに変換して返却
        return ProductDTO(
            id=product.id.value,
            name=product.name.value,
            sku=product.sku.value,
            price=product.price.value,
            category=product.category,
            description=product.description,
            stock_quantity=0,  # 今後の実装で在庫情報を取得
            created_at=product.created_at,
            updated_at=product.updated_at,
        )
```

**設計判断:**
- 存在しない商品IDは `ProductNotFoundError` をスロー
- 論理削除済み商品の更新はドメイン層で防止される

#### DeleteProductUseCase (`application/product/usecases/delete_product_usecase.py`)
```python
from sqlalchemy.orm import Session

from app.domain.product.repositories.product_repository import ProductRepository
from app.domain.product.repositories.order_repository import OrderRepository
from app.domain.product.value_objects.product_id import ProductId
from app.application.product.exceptions import ProductNotFoundError, ProductInUseError


class DeleteProductUseCase:
    """商品削除ユースケース"""

    def __init__(
        self,
        product_repository: ProductRepository,
        order_repository: OrderRepository,
        db: Session,
    ):
        self.product_repository = product_repository
        self.order_repository = order_repository
        self.db = db

    def execute(self, product_id: str) -> None:
        """商品を削除する（論理削除）"""
        # 商品を取得
        product = self.product_repository.find_by_id(ProductId(product_id))
        if product is None:
            raise ProductNotFoundError(f"Product with ID '{product_id}' not found")

        # 未完了注文チェック
        if self.order_repository.exists_active_order_with_product(product.id):
            raise ProductInUseError(
                f"Product '{product_id}' cannot be deleted because it is in active orders"
            )

        # 論理削除
        product.delete()

        # 永続化
        try:
            self.product_repository.save(product)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e
```

**設計判断:**
- 削除チェックはApplication層で実施（複数集約の協調）
- 論理削除のロジックはドメイン層（`Product.delete()`）にカプセル化

### 3.3 Application層例外

#### exceptions.py (`application/product/exceptions.py`)
```python
class ProductApplicationError(Exception):
    """商品Application層例外の基底クラス"""
    pass


class ProductNotFoundError(ProductApplicationError):
    """商品が見つからないエラー"""
    pass


class DuplicateSKUError(ProductApplicationError):
    """SKU重複エラー"""
    pass


class ProductInUseError(ProductApplicationError):
    """使用中商品の削除エラー"""
    pass
```

---

## 4. Presentation層（プレゼンテーション層）

### 4.1 Pydanticスキーマ

#### product.py (`schemas/product.py`)
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProductBase(BaseModel):
    """商品基底スキーマ"""
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ProductCreateRequest(ProductBase):
    """商品登録リクエスト"""
    sku: str = Field(..., min_length=1, max_length=50, pattern=r"^[A-Za-z0-9\-]+$")
    price: int = Field(..., ge=0)
    initial_stock: int = Field(..., ge=0)


class ProductUpdateRequest(ProductBase):
    """商品更新リクエスト"""
    price: int = Field(..., ge=0)


class ProductResponse(ProductBase):
    """商品レスポンス"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    sku: str
    price: int
    stock_quantity: int
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    """商品一覧レスポンス"""
    data: list[ProductResponse]
    pagination: "PaginationResponse"


class PaginationResponse(BaseModel):
    """ページネーションレスポンス"""
    total: int
    page: int
    per_page: int
```

**設計判断:**
- Pydantic v2の `Field` でバリデーション定義
- レスポンスは入れ子構造（`data` と `pagination`）

### 4.2 FastAPIルーター

#### products.py (`api/v1/endpoints/products.py`)
```python
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductResponse,
    ProductListResponse,
    PaginationResponse,
)
from app.application.product.usecases.list_products_usecase import ListProductsUseCase
from app.application.product.usecases.register_product_usecase import RegisterProductUseCase
from app.application.product.usecases.update_product_usecase import UpdateProductUseCase
from app.application.product.usecases.delete_product_usecase import DeleteProductUseCase
from app.application.product.dtos.product_dto import (
    RegisterProductInputDTO,
    UpdateProductInputDTO,
)
from app.application.product.exceptions import (
    ProductNotFoundError,
    DuplicateSKUError,
    ProductInUseError,
)
from app.infrastructure.repositories.product_repository import ProductRepositoryImpl
from app.infrastructure.repositories.stock_repository import StockRepositoryImpl
from app.infrastructure.repositories.order_repository import OrderRepositoryImpl


router = APIRouter()


@router.get("/", response_model=ProductListResponse)
def list_products(
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """商品一覧取得"""
    product_repository = ProductRepositoryImpl(db)
    usecase = ListProductsUseCase(product_repository)

    try:
        product_dtos, pagination_dto = usecase.execute(category, page, per_page)

        return ProductListResponse(
            data=[ProductResponse(**dto.__dict__) for dto in product_dtos],
            pagination=PaginationResponse(**pagination_dto.__dict__),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def register_product(
    request: ProductCreateRequest,
    db: Session = Depends(get_db),
):
    """商品登録"""
    product_repository = ProductRepositoryImpl(db)
    stock_repository = StockRepositoryImpl(db)
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
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: str,
    request: ProductUpdateRequest,
    db: Session = Depends(get_db),
):
    """商品更新"""
    product_repository = ProductRepositoryImpl(db)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
):
    """商品削除"""
    product_repository = ProductRepositoryImpl(db)
    order_repository = OrderRepositoryImpl(db)
    usecase = DeleteProductUseCase(product_repository, order_repository, db)

    try:
        usecase.execute(product_id)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProductInUseError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
```

**設計判断:**
- 各エンドポイントでリポジトリとUseCaseを組み立てる（DI）
- Application層の例外をHTTPステータスコードにマッピング
- `Query` でクエリパラメータのバリデーション

### 4.3 ルーター登録

#### router.py（変更） (`api/v1/router.py`)
```python
from fastapi import APIRouter
from app.api.v1.endpoints import health, examples, products  # productsを追加

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(examples.router, prefix="/examples", tags=["examples"])
api_router.include_router(products.router, prefix="/products", tags=["products"])  # 追加
```

---

## 変更するコンポーネント

### 新規作成ファイル
- Domain層: 27ファイル（エンティティ、値オブジェクト、リポジトリIF、例外）
- Application層: 10ファイル（DTO、UseCase、例外）
- Infrastructure層: 3ファイル（リポジトリ実装）
- Presentation層: 2ファイル（スキーマ、ルーター）
- Alembicマイグレーション: 1ファイル
- テスト: 11ファイル

### 既存ファイルへの変更
- `backend/app/infrastructure/database/models.py` — `ProductModel` と `StockModel` を追加
- `backend/app/api/v1/router.py` — `/products` ルーターを登録

---

## データ構造の変更

### Alembicマイグレーション実行
```bash
# マイグレーションファイル自動生成
alembic revision --autogenerate -m "create products and stocks tables"

# マイグレーション実行
alembic upgrade head
```

### 作成されるテーブル
1. **products** — 商品マスタ
2. **stocks** — 在庫マスタ

---

## 影響範囲の分析

### 既存コンポーネントへの影響
- **既存のExample実装**: 影響なし（独立したエンドポイント）
- **データベース**: 新規テーブル追加のみ（既存テーブルへの変更なし）
- **依存ライブラリ**: 追加なし（既存のFastAPI、SQLAlchemy、Pydanticで実装可能）

### 今後の実装への影響
- **在庫エンドポイント**: `Stock` 集約の完全な実装（引当・解放機能）が必要
- **注文エンドポイント**: `OrderRepository.exists_active_order_with_product()` の実装が必要
- **顧客エンドポイント**: 独立して実装可能（商品・在庫に依存しない）

### スタブ実装の完成タイミング
| コンポーネント | 今回の実装 | 完成タイミング |
|------------|----------|------------|
| `StockRepository.find_by_product_id()` | スタブ（NotImplementedError） | 在庫エンドポイント実装時 |
| `OrderRepository.exists_active_order_with_product()` | スタブ（常にFalse） | 注文エンドポイント実装時 |

---

## テスト戦略

### 1. Domain層テスト（単体テスト）

#### 目標カバレッジ: 80%以上

**テスト対象:**
- 値オブジェクトのバリデーション
- エンティティのファクトリメソッド
- エンティティのコマンドメソッド
- ドメイン例外

**テストファイル:**
```
tests/unit/domain/product/
├── test_product_entity.py           # Product.create(), update(), delete()
├── test_product_value_objects.py    # ProductId, ProductName, SKU, Price
└── test_stock_entity.py             # Stock.initialize()
```

**テスト例:**
```python
# tests/unit/domain/product/test_product_entity.py

def test_create_product():
    """商品を生成できる"""
    product = Product.create(
        name=ProductName("Test Product"),
        sku=SKU("TEST-001"),
        price=Price(1000),
        category="Electronics",
        description="Test description",
    )

    assert product.id is not None
    assert product.name.value == "Test Product"
    assert product.sku.value == "TEST-001"
    assert product.price.value == 1000
    assert product.deleted_at is None


def test_update_deleted_product_raises_error():
    """削除済み商品の更新は失敗する"""
    product = Product.create(
        name=ProductName("Test Product"),
        sku=SKU("TEST-001"),
        price=Price(1000),
        category="Electronics",
    )
    product.delete()

    with pytest.raises(ValueError, match="Cannot update a deleted product"):
        product.update(
            name=ProductName("Updated Product"),
            price=Price(2000),
            category="Electronics",
            description=None,
        )
```

### 2. Application層テスト（単体テスト）

#### 目標カバレッジ: 80%以上

**テスト対象:**
- UseCaseの正常系
- UseCaseのエラーケース（SKU重複、商品未存在、削除済み商品の更新等）
- トランザクション境界

**テストファイル:**
```
tests/unit/application/product/
├── test_list_products_usecase.py
├── test_register_product_usecase.py
├── test_update_product_usecase.py
└── test_delete_product_usecase.py
```

**テスト例:**
```python
# tests/unit/application/product/test_register_product_usecase.py

def test_register_product_success(mock_product_repository, mock_stock_repository, mock_db):
    """商品登録が成功する"""
    mock_product_repository.find_by_sku.return_value = None

    usecase = RegisterProductUseCase(mock_product_repository, mock_stock_repository, mock_db)

    input_dto = RegisterProductInputDTO(
        name="Test Product",
        sku="TEST-001",
        price=1000,
        category="Electronics",
        description="Test",
        initial_stock=100,
    )

    result = usecase.execute(input_dto)

    assert result.name == "Test Product"
    assert result.sku == "TEST-001"
    assert result.price == 1000
    assert result.stock_quantity == 100
    mock_product_repository.save.assert_called_once()
    mock_stock_repository.save.assert_called_once()
    mock_db.commit.assert_called_once()


def test_register_product_with_duplicate_sku_raises_error(mock_product_repository, mock_stock_repository, mock_db):
    """SKU重複時はエラーを返す"""
    existing_product = Product.create(
        name=ProductName("Existing Product"),
        sku=SKU("TEST-001"),
        price=Price(1000),
        category="Electronics",
    )
    mock_product_repository.find_by_sku.return_value = existing_product

    usecase = RegisterProductUseCase(mock_product_repository, mock_stock_repository, mock_db)

    input_dto = RegisterProductInputDTO(
        name="New Product",
        sku="TEST-001",
        price=2000,
        category="Electronics",
        description=None,
        initial_stock=50,
    )

    with pytest.raises(DuplicateSKUError):
        usecase.execute(input_dto)
```

### 3. Integration層テスト（統合テスト）

#### 目標カバレッジ: 主要なエンドポイントをカバー

**テスト対象:**
- APIエンドポイントの正常系
- HTTPステータスコード
- レスポンス構造
- エラーレスポンス

**テストファイル:**
```
tests/integration/api/v1/
└── test_products_endpoint.py
```

**テスト例:**
```python
# tests/integration/api/v1/test_products_endpoint.py

def test_register_product_returns_201(client, db):
    """商品登録が201を返す"""
    response = client.post(
        "/api/v1/products",
        json={
            "name": "Test Product",
            "sku": "TEST-001",
            "price": 1000,
            "category": "Electronics",
            "description": "Test",
            "initial_stock": 100,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["sku"] == "TEST-001"
    assert data["price"] == 1000
    assert data["stock_quantity"] == 100


def test_register_product_with_duplicate_sku_returns_409(client, db):
    """SKU重複時は409を返す"""
    # 1件目の登録
    client.post(
        "/api/v1/products",
        json={
            "name": "Product 1",
            "sku": "TEST-001",
            "price": 1000,
            "category": "Electronics",
            "initial_stock": 100,
        },
    )

    # 2件目の登録（SKU重複）
    response = client.post(
        "/api/v1/products",
        json={
            "name": "Product 2",
            "sku": "TEST-001",
            "price": 2000,
            "category": "Electronics",
            "initial_stock": 50,
        },
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]
```

### 4. Repository層テスト（統合テスト）

**テスト対象:**
- リポジトリ実装とデータベースの統合
- ORMマッピングの正確性
- ページネーション機能

**テストファイル:**
```
tests/integration/infrastructure/
└── test_product_repository.py
```

**テスト例:**
```python
# tests/integration/infrastructure/test_product_repository.py

def test_save_and_find_by_id(db):
    """商品を保存して取得できる"""
    repository = ProductRepositoryImpl(db)

    product = Product.create(
        name=ProductName("Test Product"),
        sku=SKU("TEST-001"),
        price=Price(1000),
        category="Electronics",
    )

    repository.save(product)
    db.commit()

    found = repository.find_by_id(product.id)

    assert found is not None
    assert found.id.value == product.id.value
    assert found.name.value == "Test Product"
    assert found.sku.value == "TEST-001"
```

### テスト実行コマンド
```bash
# 全テスト実行
pytest

# Domain層テストのみ
pytest tests/unit/domain/

# Application層テストのみ
pytest tests/unit/application/

# 統合テストのみ
pytest tests/integration/

# カバレッジレポート生成
pytest --cov=app --cov-report=html
```

---

## 実装時の注意事項

### 1. ドメイン層の純粋性
- ドメイン層は外部ライブラリ（FastAPI、SQLAlchemy等）に依存しない
- `import sqlalchemy` や `import fastapi` がドメイン層に存在しないことを確認

### 2. 値オブジェクトの不変性
- `@dataclass(frozen=True)` で不変性を保証する
- バリデーションは `__post_init__` で実施する

### 3. トランザクション境界
- Application層（UseCase）でトランザクションを制御する
- `db.commit()` と `db.rollback()` をUseCaseで呼び出す

### 4. エラーハンドリング
- ドメイン例外はApplication層でキャッチし、Application層例外に変換する
- Application層例外はPresentation層でキャッチし、HTTPステータスコードにマッピングする

### 5. IDの生成
- UUIDはドメイン層で生成する（`ProductId.generate()`）
- データベース側でIDを自動採番しない

### 6. ページネーションの実装
- `page` と `per_page` のバリデーションをApplication層で実施
- `per_page` の上限を100に制限

### 7. 論理削除の扱い
- `deleted_at` が `NULL` のレコードのみ取得する
- リポジトリの `find_*()` メソッドで論理削除フィルタを適用

### 8. スタブ実装の明示
- 今後実装する予定のメソッドには `NotImplementedError` をスローする
- スタブ実装であることをコメントで明記する

---

## まとめ

本設計書では、OrderHub（注文管理システム）の商品エンドポイントをDDDレイヤードアーキテクチャに基づいて実装する詳細な設計を定義した。

**実装の要点:**
1. **4層アーキテクチャ**: Presentation / Application / Domain / Infrastructure の責務を明確に分離
2. **純粋なドメインモデル**: ドメイン層は外部ライブラリに依存しない
3. **値オブジェクトによるバリデーション**: 不正な値の生成を防止
4. **トランザクション境界の明確化**: Application層でトランザクションを制御
5. **テスト戦略**: 各層で80%以上のカバレッジを目標

**次のステップ:**
- tasklist.mdの作成
- 実装の開始（Domain層 → Infrastructure層 → Application層 → Presentation層の順）
- 各層のテスト実装
- 統合テストの実施
