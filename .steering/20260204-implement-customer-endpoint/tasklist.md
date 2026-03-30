# タスクリスト: 顧客エンドポイント実装

## 概要
OrderHub（注文管理システム）の顧客エンドポイントをDDDレイヤードアーキテクチャに基づいて実装する。
実装順序: Domain層 → Infrastructure層 → Application層 → Presentation層 → テスト

---

## Phase 1: Domain層の実装

### 1.1 顧客集約の値オブジェクト
- [x] `backend/app/domain/customer/__init__.py` 作成
- [x] `backend/app/domain/customer/value_objects/__init__.py` 作成
- [x] `backend/app/domain/customer/value_objects/customer_id.py` 作成
  - CustomerIdクラス（UUID文字列、空チェック、`generate()`メソッド）
- [x] `backend/app/domain/customer/value_objects/customer_name.py` 作成
  - CustomerNameクラス（1〜100文字、空チェック）
- [x] `backend/app/domain/customer/value_objects/email_address.py` 作成
  - EmailAddressクラス（RFC準拠のパターン検証、1〜255文字）
- [x] `backend/app/domain/customer/value_objects/member_rank.py` 作成
  - MemberRankクラス（BRONZE/SILVER/GOLDの列挙型、`default()`メソッド）
- [x] `backend/app/domain/customer/value_objects/address.py` 作成
  - Addressクラス（郵便番号NNN-NNNN形式、都道府県、市区町村、番地）

### 1.2 顧客エンティティ
- [x] `backend/app/domain/customer/entities/__init__.py` 作成
- [x] `backend/app/domain/customer/entities/shipping_address.py` 作成
  - ShippingAddressクラス（集約内エンティティ）
  - ファクトリメソッド: `create()`
- [x] `backend/app/domain/customer/entities/customer.py` 作成
  - Customerクラス（集約ルート）
  - ファクトリメソッド: `create()`
  - コマンドメソッド: `update()`, `add_shipping_address()`, `get_shipping_address()`, `get_default_address()`
  - 不変条件: 配送先住所最大5件、デフォルト住所の一意性

### 1.3 リポジトリインターフェース
- [x] `backend/app/domain/customer/repositories/__init__.py` 作成
- [x] `backend/app/domain/customer/repositories/customer_repository.py` 作成
  - ICustomerRepositoryインターフェース（ABC）
  - メソッド: `find_by_id()`, `find_by_email()`, `save()`
- [x] `backend/app/domain/product/repositories/order_repository.py` 変更
  - IOrderRepositoryインターフェースに `find_by_customer_id()` メソッド追加
  - 既存の `exists_active_order_with_product()` は維持

### 1.4 ドメイン例外
- [x] `backend/app/domain/customer/exceptions.py` 作成
  - CustomerDomainError（基底クラス）
  - MaxAddressLimitExceededError
  - ShippingAddressNotFoundError
  - InvalidEmailFormatError
  - InvalidPostalCodeFormatError

---

## Phase 2: Infrastructure層の実装

### 2.1 SQLAlchemyモデル定義
- [x] `backend/app/infrastructure/database/models.py` 変更
  - CustomerModelクラス追加（`customers`テーブル）
  - ShippingAddressModelクラス追加（`shipping_addresses`テーブル）
  - リレーション定義（Eager Loading設定）
  - CHECK制約、UNIQUE制約、インデックス定義

### 2.2 リポジトリ実装
- [x] `backend/app/infrastructure/repositories/customer_repository.py` 作成
  - CustomerRepositoryクラス
  - 実装メソッド: `find_by_id()`, `find_by_email()`, `save()`
  - プライベートメソッド: `_to_entity()`（ORMモデル → ドメインエンティティ変換）
- [x] `backend/app/infrastructure/repositories/order_repository.py` 変更
  - OrderRepositoryクラスに `find_by_customer_id()` メソッド追加
  - スタブメソッド: `find_by_customer_id()`（空のリストと総件数0を返す）

### 2.3 Alembicマイグレーション
- [ ] Alembicマイグレーションファイル自動生成
- [ ] 生成されたマイグレーションファイルのレビューと調整
- [ ] マイグレーション実行

---

## Phase 3: Application層の実装

### 3.1 DTO定義
- [x] `backend/app/application/customer/__init__.py` 作成
- [x] `backend/app/application/customer/dtos/__init__.py` 作成
- [x] `backend/app/application/customer/dtos/customer_dto.py` 作成
- [x] `backend/app/application/customer/dtos/order_dto.py` 作成

### 3.2 UseCase実装
- [x] `backend/app/application/customer/usecases/__init__.py` 作成
- [x] `backend/app/application/customer/usecases/get_customer_usecase.py` 作成
- [x] `backend/app/application/customer/usecases/register_customer_usecase.py` 作成
- [x] `backend/app/application/customer/usecases/update_customer_usecase.py` 作成
- [x] `backend/app/application/customer/usecases/add_shipping_address_usecase.py` 作成
- [x] `backend/app/application/customer/usecases/list_customer_orders_usecase.py` 作成

### 3.3 Application層例外
- [x] `backend/app/application/customer/exceptions.py` 作成

---

## Phase 4: Presentation層の実装

### 4.1 Pydanticスキーマ定義
- [x] `backend/app/schemas/customer.py` 作成

### 4.2 FastAPIルーター実装
- [x] `backend/app/api/v1/endpoints/customers.py` 作成

### 4.3 ルーター登録
- [x] `backend/app/api/v1/router.py` 変更

---

## Phase 5: テストの実装

### 5.1 Domain層テスト（単体テスト）
- [x] `backend/tests/unit/domain/customer/__init__.py` 作成
- [x] `backend/tests/unit/domain/customer/test_customer_value_objects.py` 作成（27テスト）
- [x] `backend/tests/unit/domain/customer/test_shipping_address_entity.py` 作成（3テスト）
- [x] `backend/tests/unit/domain/customer/test_customer_entity.py` 作成（10テスト）

### 5.2 Application層テスト（単体テスト）
- [x] `backend/tests/unit/application/customer/__init__.py` 作成
- [x] `backend/tests/unit/mocks/mock_customer_repository.py` 作成
- [x] `backend/tests/unit/mocks/mock_order_repository.py` 変更（`find_by_customer_id()`追加）
- [x] `backend/tests/unit/application/customer/test_get_customer_usecase.py` 作成（2テスト）
- [x] `backend/tests/unit/application/customer/test_register_customer_usecase.py` 作成（4テスト）
- [x] `backend/tests/unit/application/customer/test_update_customer_usecase.py` 作成（4テスト）
- [x] `backend/tests/unit/application/customer/test_add_shipping_address_usecase.py` 作成（4テスト）
- [x] `backend/tests/unit/application/customer/test_list_customer_orders_usecase.py` 作成（2テスト）

### 5.3 Integration層テスト（統合テスト）
- [x] `backend/tests/integration/api/v1/test_customers_endpoint.py` 作成（10テスト）

### 5.4 Repository層テスト（統合テスト）
- [ ] `backend/tests/integration/infrastructure/test_customer_repository.py` 作成

---

## Phase 6: 品質チェック

### 6.1 テストカバレッジ確認
- [ ] テストカバレッジレポート生成
- [ ] Domain層カバレッジ80%以上を確認
- [ ] Application層カバレッジ80%以上を確認

### 6.2 コード品質チェック
- [ ] Ruffによるリンティング実行
- [ ] 型チェック実行（mypyがあれば）

### 6.3 手動動作確認
- [ ] Swagger UIでAPI仕様確認
- [ ] 各エンドポイントの動作確認

---

## テスト実行結果

### 単体テスト: 55 passed
- Domain層: 40テスト（値オブジェクト27、ShippingAddress 3、Customer 10）
- Application層: 16テスト（GetCustomer 2、Register 4、Update 4、AddAddress 4、ListOrders 2）

### 統合テスト: 10 passed
- POST /customers: 2テスト（正常系、メールアドレス重複）
- GET /customers/{id}: 2テスト（正常系、未存在）
- PUT /customers/{id}: 2テスト（正常系、未存在）
- POST /customers/{id}/addresses: 2テスト（正常系、未存在）
- GET /customers/{id}/orders: 2テスト（正常系スタブ、未存在）

### 全テスト: 137 passed, 1 failed（既知のhealth checkテスト）

---

## 備考

### IOrderRepositoryの配置について
- 設計上は`domain/order/`に分離する案もあったが、既存コード（`domain/product/repositories/order_repository.py`）との後方互換性を維持するため、既存インターフェースに`find_by_customer_id()`を追加する方式を採用した
- 注文エンドポイント実装時に、必要に応じてリファクタリングする

### email-validatorの追加
- Pydanticの`EmailStr`型を使用するため、`email-validator`パッケージを追加した

### 商品エンドポイントとの違い
- **集約内エンティティ**: ShippingAddressは独自リポジトリを持たない（Customer経由でのみアクセス）
- **論理削除**: 顧客は論理削除しない（商品のような`deleted_at`は不要）
- **リレーション**: Customer-ShippingAddress間に外部キー制約を設定（集約内の整合性保証）
- **Eager Loading**: CustomerとShippingAddressを一緒に取得（N+1問題回避）
- **ドメインルール**: 配送先住所最大5件、デフォルト住所の一意性をドメイン層で強制
