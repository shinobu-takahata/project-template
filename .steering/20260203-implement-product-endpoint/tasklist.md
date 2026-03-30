# タスクリスト: 商品エンドポイント実装

## 概要
OrderHub（注文管理システム）の商品エンドポイントをDDDレイヤードアーキテクチャに基づいて実装する。
実装順序: Domain層 → Infrastructure層 → Application層 → Presentation層 → テスト

---

## Phase 1: Domain層の実装

### 1.1 商品集約の値オブジェクト
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/product/__init__.py` 作成
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/product/value_objects/__init__.py` 作成
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/product/value_objects/product_id.py` 作成
  - ProductIdクラス（UUID文字列、空チェック、`generate()`メソッド）
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/product/value_objects/product_name.py` 作成
  - ProductNameクラス（1〜200文字、空チェック）
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/product/value_objects/sku.py` 作成
  - SKUクラス（1〜50文字、パターン `^[A-Za-z0-9\-]+$`）
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/product/value_objects/price.py` 作成
  - Priceクラス（0以上の整数）

### 1.2 在庫集約の値オブジェクト
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/stock/__init__.py` 作成
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/stock/value_objects/__init__.py` 作成
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/stock/value_objects/stock_id.py` 作成
  - StockIdクラス（UUID文字列、空チェック、`generate()`メソッド）
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/stock/value_objects/stock_quantity.py` 作成
  - StockQuantityクラス（0以上の整数）

### 1.3 商品エンティティ
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/product/entities/__init__.py` 作成
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/product/entities/product.py` 作成
  - Productクラス（集約ルート）
  - ファクトリメソッド: `create()`
  - コマンドメソッド: `update()`, `delete()`
  - プロパティ: `is_deleted`

### 1.4 在庫エンティティ
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/stock/entities/__init__.py` 作成
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/stock/entities/stock.py` 作成
  - Stockクラス（集約ルート）
  - ファクトリメソッド: `initialize()`（初期在庫作成用）

### 1.5 リポジトリインターフェース
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/product/repositories/__init__.py` 作成
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/product/repositories/product_repository.py` 作成
  - ProductRepositoryインターフェース（ABC）
  - メソッド: `find_by_id()`, `find_by_sku()`, `find_all()`, `save()`
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/stock/repositories/__init__.py` 作成
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/stock/repositories/stock_repository.py` 作成
  - StockRepositoryインターフェース（ABC）
  - メソッド: `save()`, `find_by_product_id()`（スタブ実装予定）
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/product/repositories/order_repository.py` 作成
  - OrderRepositoryインターフェース（ABC）
  - メソッド: `exists_active_order_with_product()`（スタブ実装予定）

### 1.6 ドメイン例外
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/domain/product/exceptions.py` 作成
  - ProductDomainError（基底クラス）
  - ProductAlreadyDeletedError
  - InvalidPriceError
  - InvalidSKUFormatError

---

## Phase 2: Infrastructure層の実装

### 2.1 SQLAlchemyモデル定義
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/infrastructure/database/models.py` 変更
  - ProductModelクラス追加（`products`テーブル）
  - StockModelクラス追加（`stocks`テーブル）
  - CHECK制約、UNIQUE制約、インデックス定義

### 2.2 リポジトリ実装
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/infrastructure/repositories/product_repository.py` 作成
  - ProductRepositoryImplクラス
  - 実装メソッド: `find_by_id()`, `find_by_sku()`, `find_all()`, `save()`
  - プライベートメソッド: `_to_entity()`（ORMモデル → ドメインエンティティ変換）
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/infrastructure/repositories/stock_repository.py` 作成
  - StockRepositoryImplクラス
  - 実装メソッド: `save()`, `find_by_product_id()`
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/infrastructure/repositories/order_repository.py` 作成
  - OrderRepositoryImplクラス
  - スタブメソッド: `exists_active_order_with_product()`（常に`False`を返す）

### 2.3 Alembicマイグレーション
- [ ] Alembicマイグレーションファイル自動生成
  - `alembic revision --autogenerate -m "create products and stocks tables"`
- [ ] 生成されたマイグレーションファイルのレビューと調整
- [ ] マイグレーション実行
  - `alembic upgrade head`

---

## Phase 3: Application層の実装

### 3.1 DTO定義
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/application/product/__init__.py` 作成
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/application/product/dtos/__init__.py` 作成
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/application/product/dtos/product_dto.py` 作成
  - ProductDTOクラス（商品DTO）
  - RegisterProductInputDTOクラス（商品登録入力DTO）
  - UpdateProductInputDTOクラス（商品更新入力DTO）
  - PaginationDTOクラス（ページネーションDTO）

### 3.2 UseCase実装
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/application/product/usecases/__init__.py` 作成
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/application/product/usecases/list_products_usecase.py` 作成
  - ListProductsUseCaseクラス
  - `execute()`メソッド（カテゴリフィルタ、ページネーション対応）
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/application/product/usecases/register_product_usecase.py` 作成
  - RegisterProductUseCaseクラス
  - `execute()`メソッド（SKU重複チェック、商品+在庫トランザクション）
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/application/product/usecases/update_product_usecase.py` 作成
  - UpdateProductUseCaseクラス
  - `execute()`メソッド（存在チェック、更新処理）
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/application/product/usecases/delete_product_usecase.py` 作成
  - DeleteProductUseCaseクラス
  - `execute()`メソッド（存在チェック、注文使用中チェック、論理削除）

### 3.3 Application層例外
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/application/product/exceptions.py` 作成
  - ProductApplicationError（基底クラス）
  - ProductNotFoundError
  - DuplicateSKUError
  - ProductInUseError

---

## Phase 4: Presentation層の実装

### 4.1 Pydanticスキーマ定義
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/schemas/product.py` 作成
  - ProductBaseクラス（基底スキーマ）
  - ProductCreateRequestクラス（商品登録リクエスト）
  - ProductUpdateRequestクラス（商品更新リクエスト）
  - ProductResponseクラス（商品レスポンス）
  - ProductListResponseクラス（商品一覧レスポンス）
  - PaginationResponseクラス（ページネーションレスポンス）

### 4.2 FastAPIルーター実装
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/api/v1/endpoints/products.py` 作成
  - `GET /api/v1/products` エンドポイント（商品一覧取得）
  - `POST /api/v1/products` エンドポイント（商品登録）
  - `PUT /api/v1/products/{product_id}` エンドポイント（商品更新）
  - `DELETE /api/v1/products/{product_id}` エンドポイント（商品削除）
  - エラーハンドリング（Application層例外 → HTTPステータスコード）

### 4.3 ルーター登録
- [x] `/Users/shinobu-takahata/app/project-template/backend/app/api/v1/router.py` 変更
  - `products.router` を `/products` パスで登録

---

## Phase 5: テストの実装

### 5.1 Domain層テスト（単体テスト）
- [x] `/Users/shinobu-takahata/app/project-template/backend/tests/unit/domain/product/__init__.py` 作成
- [x] `/Users/shinobu-takahata/app/project-template/backend/tests/unit/domain/product/test_product_value_objects.py` 作成
  - ProductId, ProductName, SKU, Priceのバリデーションテスト
- [x] `/Users/shinobu-takahata/app/project-template/backend/tests/unit/domain/product/test_product_entity.py` 作成
  - `Product.create()` のテスト
  - `product.update()` のテスト（正常系・エラー系）
  - `product.delete()` のテスト（正常系・エラー系）
- [x] `/Users/shinobu-takahata/app/project-template/backend/tests/unit/domain/stock/__init__.py` 作成
- [x] `/Users/shinobu-takahata/app/project-template/backend/tests/unit/domain/stock/test_stock_entity.py` 作成
  - `Stock.initialize()` のテスト

### 5.2 Application層テスト（単体テスト）
- [x] `/Users/shinobu-takahata/app/project-template/backend/tests/unit/application/product/__init__.py` 作成
- [x] `/Users/shinobu-takahata/app/project-template/backend/tests/unit/mocks/mock_product_repository.py` 作成
  - モックProductRepository実装
- [x] `/Users/shinobu-takahata/app/project-template/backend/tests/unit/mocks/mock_stock_repository.py` 作成
  - モックStockRepository実装
- [x] `/Users/shinobu-takahata/app/project-template/backend/tests/unit/mocks/mock_order_repository.py` 作成
  - モックOrderRepository実装
- [x] `/Users/shinobu-takahata/app/project-template/backend/tests/unit/application/product/test_list_products_usecase.py` 作成
  - ListProductsUseCaseの正常系テスト
  - ページネーションバリデーションテスト
- [x] `/Users/shinobu-takahata/app/project-template/backend/tests/unit/application/product/test_register_product_usecase.py` 作成
  - RegisterProductUseCaseの正常系テスト
  - SKU重複エラーテスト
  - トランザクションロールバックテスト
- [x] `/Users/shinobu-takahata/app/project-template/backend/tests/unit/application/product/test_update_product_usecase.py` 作成
  - UpdateProductUseCaseの正常系テスト
  - 商品未存在エラーテスト
  - 削除済み商品更新エラーテスト
- [x] `/Users/shinobu-takahata/app/project-template/backend/tests/unit/application/product/test_delete_product_usecase.py` 作成
  - DeleteProductUseCaseの正常系テスト
  - 商品未存在エラーテスト
  - 使用中商品削除エラーテスト

### 5.3 Integration層テスト（統合テスト）
- [x] `/Users/shinobu-takahata/app/project-template/backend/tests/integration/api/v1/__init__.py` 作成
- [x] `/Users/shinobu-takahata/app/project-template/backend/tests/integration/api/v1/test_products_endpoint.py` 作成
  - `POST /api/v1/products` のテスト（正常系・SKU重複エラー）
  - `GET /api/v1/products` のテスト（正常系・カテゴリフィルタ・ページネーション）
  - `PUT /api/v1/products/{product_id}` のテスト（正常系・未存在エラー）
  - `DELETE /api/v1/products/{product_id}` のテスト（正常系・未存在エラー）

### 5.4 Repository層テスト（統合テスト）
- [ ] `/Users/shinobu-takahata/app/project-template/backend/tests/integration/infrastructure/__init__.py` 作成
- [ ] `/Users/shinobu-takahata/app/project-template/backend/tests/integration/infrastructure/test_product_repository.py` 作成
  - `save()` と `find_by_id()` のテスト
  - `find_by_sku()` のテスト
  - `find_all()` のテスト（カテゴリフィルタ、ページネーション）
  - 論理削除フィルタのテスト

---

## Phase 6: 品質チェック

### 6.1 テストカバレッジ確認
- [ ] テストカバレッジレポート生成
  - `pytest --cov=app --cov-report=html`
- [ ] Domain層カバレッジ80%以上を確認
- [ ] Application層カバレッジ80%以上を確認

### 6.2 コード品質チェック
- [ ] Ruffによるリンティング実行
  - `ruff check .`
- [ ] 型チェック実行（mypyがあれば）
  - `mypy app/`

### 6.3 手動動作確認
- [ ] FastAPIサーバー起動確認
  - `uvicorn app.main:app --reload`
- [ ] Swagger UIでAPI仕様確認
  - `http://localhost:8000/docs`
- [ ] 商品登録エンドポイント動作確認
- [ ] 商品一覧取得エンドポイント動作確認
- [ ] 商品更新エンドポイント動作確認
- [ ] 商品削除エンドポイント動作確認

---

## 完了条件

### 機能要件
- [ ] GET /api/v1/products がカテゴリフィルタとページネーションに対応している
- [ ] POST /api/v1/products がSKU重複時に適切なエラー（`DUPLICATE_SKU`）を返す
- [ ] POST /api/v1/products が商品と初期在庫をトランザクション内で作成する
- [ ] PUT /api/v1/products が存在しない商品IDに対して`PRODUCT_NOT_FOUND`を返す
- [ ] PUT /api/v1/products が論理削除済み商品の更新を拒否する
- [ ] DELETE /api/v1/products が未完了注文に含まれる商品の削除を拒否する（`PRODUCT_IN_USE`）
- [ ] DELETE /api/v1/products が論理削除として実装され、`deleted_at`に日時が設定される

### アーキテクチャ要件
- [ ] ドメイン層が外部ライブラリ（FastAPI、SQLAlchemy等）に依存していない
- [ ] ビジネスロジック（SKU検証、価格検証、削除可否判定）がドメイン層に集約されている
- [ ] リポジトリパターンでデータアクセスが抽象化されている
- [ ] Application層がトランザクション境界を制御している
- [ ] 値オブジェクトが不変であり、バリデーションをコンストラクタで実施している

### 品質要件
- [ ] ドメイン層の単体テストカバレッジが80%以上
- [ ] Application層の単体テストカバレッジが80%以上
- [ ] 各UseCaseに対する統合テストが存在する
- [ ] エラーケースに対するテストが存在する（SKU重複、存在しない商品ID、削除済み商品の更新、使用中商品の削除）
- [ ] APIドキュメント（OpenAPI/Swagger）が自動生成される

---

## 備考

### 実装順序の理由
1. **Domain層から実装**: ビジネスロジックの中核を先に確立し、後続の層がこれに依存する形で実装
2. **Infrastructure層を次に実装**: Domain層のリポジトリインターフェースを具体化
3. **Application層で協調**: 複数の集約を協調させるビジネスユースケースを実装
4. **Presentation層で公開**: HTTPインターフェースとしてAPIを公開
5. **テストで品質保証**: 各層の実装完了後、テストで品質を担保

### スタブ実装の扱い
- `StockRepository.find_by_product_id()` → NotImplementedErrorをスロー（在庫エンドポイント実装時に完成）
- `OrderRepository.exists_active_order_with_product()` → 常に`False`を返す（注文エンドポイント実装時に完成）

### 依存関係の注意点
- ドメイン層は外部ライブラリに依存しない
- Infrastructure層はドメイン層のインターフェースに依存する
- Application層はドメイン層とInfrastructure層に依存する
- Presentation層はApplication層に依存する
