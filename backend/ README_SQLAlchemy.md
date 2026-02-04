# SQLAlchemy TIPS

## モデル定義
```python
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
	pass


class User(Base):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
	is_active: Mapped[bool] = mapped_column(default=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True), server_default=func.now()
	)
	addresses: Mapped[list["Address"]] = relationship(
		back_populates="user", lazy="selectin"
	) # back_populatesには逆方向の属性名を指定します。


class Address(Base):
	__tablename__ = "addresses"

	id: Mapped[int] = mapped_column(primary_key=True)
	user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
	postal_code: Mapped[str] = mapped_column(String(10))
	city: Mapped[str] = mapped_column(String(50))
	line1: Mapped[str] = mapped_column(String(255))
	user: Mapped[User] = relationship(back_populates="addresses")
```

## モデル定義（多対多用中間テーブル）
https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#many-to-many
```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


article_topics = Table(
	"article_topics",
	Base.metadata,
	Column("article_id", ForeignKey("articles.id"), primary_key=True),
	Column("topic_id", ForeignKey("topics.id"), primary_key=True),
)


class Article(Base):
	__tablename__ = "articles"

	id: Mapped[int] = mapped_column(primary_key=True)
	title: Mapped[str]
	body: Mapped[str]
	topics: Mapped[list["Topic"]] = relationship(
		secondary=lambda: ArticleTopic.__table__,
		back_populates="articles",
		lazy="selectin",
	)	# Article.<->Topic 双方向多対多、secondaryで中間テーブルを指定


class Topic(Base):
	__tablename__ = "topics"

	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str]
	articles: Mapped[list[Article]] = relationship(
		secondary=lambda: ArticleTopic.__table__,
		back_populates="topics",
	)	# back_populatesは必ず対になる
```

## モデル定義（Enum, Numeric）
```python
from decimal import Decimal
from enum import Enum

from sqlalchemy import Enum as SAEnum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column


class InventoryStatus(str, Enum):
	IN_STOCK = "IN_STOCK"
	OUT_OF_STOCK = "OUT_OF_STOCK"
	DISCONTINUED = "DISCONTINUED"


class Inventory(Base):
	__tablename__ = "inventories"

	id: Mapped[int] = mapped_column(primary_key=True)
	product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
	quantity: Mapped[int] = mapped_column(default=0)
	cost_price: Mapped[Decimal] = mapped_column(Numeric(12, 4))
	status: Mapped[InventoryStatus] = mapped_column(
		SAEnum(InventoryStatus, name="inventory_status")
	)
```

## 基本クエリ（select）
```python
from sqlalchemy import select

stmt = (
	select(User.id, User.email, User.created_at)
	.where(User.is_active.is_(True))
	.order_by(User.created_at.desc())
	.limit(10)
)
rows = session.execute(stmt).all()

for user_id, email, created_at in rows:
	print(f"{user_id}: {email} ({created_at:%Y-%m-%d})")
```

## 基本クエリ（insert）
```python
user_payload = {
	"email": request_body["email"],
	"is_active": request_body.get("is_active", True),
}
new_user = User(**user_payload)
session.add(new_user)
session.flush()  # PKを確定させて子テーブルに流用する

address_payload = {
	"user_id": new_user.id,
	"postal_code": request_body["postal_code"],
	"city": request_body["city"],
	"line1": request_body["line1"],
}
session.add(Address(**address_payload))
session.commit()
```

## 基本クエリ（update）
```python
from sqlalchemy import update

update_values = {
	"email": request_body["email"],
	"is_active": request_body["is_active"],
	"updated_at": utc_now,
}

stmt = (
	update(User)
	.where(User.id == target_user_id)
	.values(**update_values)
	.returning(User.id, User.email)
)
session.execute(stmt)
session.commit()
```

## 基本クエリ（delete）
```python
from sqlalchemy import delete

stmt = delete(Address).where(Address.user_id == target_user_id)
session.execute(stmt)
session.commit()
```

## リレーションシップ読み込みテクニック
https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#relationship-loading-with-loader-options

リレーションシップの読み込みは、遅延読み込み（lazy loading）、即時読み込み（eager loading）、非読み込み（no loading）の3種類に分類されます。ここでは、lazy, eagerの2つをおさえます。

### lazy load
https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#select-in-loading


lazy loadとは、クエリから関連オブジェクトを最初に読み込まずに返されるオブジェクトを指します。


特定のオブジェクトで指定されたコレクションや参照が初めてアクセスされると、要求されたコレクションを読み込むための追加のSELECT文が生成されます。

基本的に、あえてlazy loadを使用することはないですが、関連テーブルが巨大で何個もある場合、等のケースでは、eager loadすることでSQLが巨大になりメモリも食いつぶするため、lazy loadの方が向いています。

```python
from sqlalchemy import select
from sqlalchemy.orm import load_only

stmt = (
	select(User)
	.options(load_only(User.id, User.email, User.is_active))
	.where(User.id == target_user_id)
)
user = session.scalars(stmt).one()

# addressesへ最初にアクセスした瞬間に追加SELECTが発行される
for address in user.addresses:
	print(address.city, address.line1)
```



### eager load
https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#select-in-loading
eager loadとは、関連するコレクションやスカラー参照が事前に読み込まれた状態でクエリから返されるオブジェクトを指します。

ORMはこれを実現するため、通常発行するSELECT文にJOINを追加して関連行を同時に読み込むか、主クエリの後に追加のSELECT文を発行してコレクションやスカラー参照を一括読み込みます。

```python
from sqlalchemy import select
from sqlalchemy.orm import load_only, selectinload

stmt = (
	select(User)
	.options(
		load_only(User.id, User.email),
		selectinload(User.addresses).load_only(
			Address.id, Address.city, Address.line1
		),
	)
	.where(User.is_active.is_(True))
)
users = session.scalars(stmt).all()

for user in users:
	print(user.email, "=>", [addr.city for addr in user.addresses])
```


## 列読み込みオプション
カラムを指定するためのテクニックです。
全カラムを読み込むとパフォーマンス低下につながる（体感レベルで）ため、基本的にはカラムを指定してselectをかけるようにします。

### `load_only()`メソッドを使用することでこれを解決します
https://docs.sqlalchemy.org/en/20/orm/queryguide/columns.html#column-loading-options

```python
from sqlalchemy import select
from sqlalchemy.orm import load_only

stmt = (
	select(User)
	.options(load_only(User.id, User.email))
	.where(User.is_active.is_(True))
)
active_users = session.scalars(stmt).all()
```

### select()メソッド内でカラム指定することとの違い
https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html#selecting-individual-attributes

`select(User.id, User.name)`のようにすると、返却される値は`Row`オブジェクトになります。
そのため、SQLAlchemyのモデルのインスタンスとして生成されず、補完が効かないデメリットがあります。
（`result.name`のように打ちたくても、.nameを持っているかどうか、`Row`オブジェクトがわからないです。）
（より細かく高速アクセスしたい際や、APIレスポンスとしてそのままぶちこむことがわかりきっているならアリです。）


## 集計処理
```python
from sqlalchemy import func, select

stmt = (
	select(
		Address.city,
		func.count(Address.id).label("address_count"),
	)
	.group_by(Address.city)
	.having(func.count(Address.id) > 5)
	.order_by(func.count(Address.id).desc())
)

for city, count in session.execute(stmt):
	print(city, count)
```
