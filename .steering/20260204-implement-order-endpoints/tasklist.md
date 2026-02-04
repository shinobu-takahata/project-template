# タスクリスト: 注文エンドポイント実装

## タスク一覧

### フェーズ1: Domain層の実装

#### 1.1 値オブジェクトの作成
- [x]OrderId値オブジェクトの実装
  - ファイル: `backend/app/domain/order/value_objects/order_id.py`
  - 内容: UUID生成、空文字バリデーション
  - 完了条件: OrderIdが生成でき、空文字時に例外が発生すること

- [x]Money値オブジェクトの実装
  - ファイル: `backend/app/domain/order/value_objects/money.py`
  - 内容: 金額計算（加算、減算、乗算、消費税計算）、負数バリデーション
  - 完了条件: 四則演算が正しく動作し、負数時に例外が発生すること

- [x]OrderStatus値オブジェクトの実装
  - ファイル: `backend/app/domain/order/value_objects/order_status.py`
  - 内容: ステータス定義、遷移ルール、キャンセル可否判定
  - 完了条件: ステータス遷移の妥当性が正しく判定されること

- [x]ShippingAddress値オブジェクトの実装
  - ファイル: `backend/app/domain/order/value_objects/shipping_address.py`
  - 内容: 郵便番号形式バリデーション、住所各項目の必須チェック
  - 完了条件: 郵便番号がNNN-NNNN形式でない場合に例外が発生すること

- [x]__init__.pyファイルの作成
  - ファイル: `backend/app/domain/order/value_objects/__init__.py`
  - 内容: 空ファイル（Pythonパッケージとして認識させる）
  - 完了条件: ファイルが存在すること

#### 1.2 エンティティの作成
- [x]OrderItemエンティティの実装
  - ファイル: `backend/app/domain/order/entities/order_item.py`
  - 内容: 注文明細、小計計算、数量バリデーション
  - 依存: Money、ProductId値オブジェクト
  - 完了条件: 小計が正しく計算され、数量0以下で例外が発生すること

- [x]Orderエンティティの実装（集約ルート）
  - ファイル: `backend/app/domain/order/entities/order.py`
  - 内容: 注文生成ファクトリメソッド、ステータス遷移、キャンセル処理
  - 依存: OrderId、OrderStatus、Money、ShippingAddress、OrderItem、CustomerId
  - 完了条件: 注文生成、ステータス遷移、キャンセル処理が正しく動作すること

- [x]__init__.pyファイルの作成
  - ファイル: `backend/app/domain/order/entities/__init__.py`
  - 内容: 空ファイル
  - 完了条件: ファイルが存在すること

#### 1.3 ドメインサービスの作成
- [x]DiscountPolicyの実装
  - ファイル: `backend/app/domain/order/services/discount_policy.py`
  - 内容: 会員ランク割引、数量割引、クーポン割引の計算ロジック
  - 依存: Money、MemberRank
  - 完了条件: 各割引が正しく計算されること

- [x]OrderDomainServiceの実装
  - ファイル: `backend/app/domain/order/services/order_domain_service.py`
  - 内容: 注文生成ロジック、割引適用順序、税込合計金額計算
  - 依存: Order、OrderItem、Money、ShippingAddress、DiscountPolicy、Customer、Product
  - 完了条件: 注文が正しく生成され、金額計算が仕様通りであること

- [x]__init__.pyファイルの作成
  - ファイル: `backend/app/domain/order/services/__init__.py`
  - 内容: 空ファイル
  - 完了条件: ファイルが存在すること

#### 1.4 リポジトリインターフェースの作成
- [x]IOrderRepositoryインターフェースの実装
  - ファイル: `backend/app/domain/order/repositories/order_repository.py`
  - 内容: save、find_by_id、find_by_customer_id、exists_active_order_with_productメソッド定義
  - 依存: Order、OrderId、CustomerId
  - 完了条件: インターフェースが定義されていること

- [x]__init__.pyファイルの作成
  - ファイル: `backend/app/domain/order/repositories/__init__.py`
  - 内容: 空ファイル
  - 完了条件: ファイルが存在すること

#### 1.5 ドメイン例外の作成
- [x]注文ドメイン例外の実装
  - ファイル: `backend/app/domain/order/exceptions.py`
  - 内容: OrderDomainError、InsufficientStockError、InvalidStatusTransitionError、OrderCannotBeCancelledError
  - 完了条件: 各例外クラスが定義されていること

- [x]__init__.pyファイルの作成
  - ファイル: `backend/app/domain/order/__init__.py`
  - 内容: 空ファイル
  - 完了条件: ファイルが存在すること

---

### フェーズ2: Infrastructure層の実装

#### 2.1 SQLAlchemyモデルの作成
- [x]OrderModelの実装
  - ファイル: `backend/app/infrastructure/database/models.py`（既存ファイルに追加）
  - 内容: ordersテーブル定義、インデックス、CHECK制約、リレーション設定
  - 完了条件: OrderModelが定義され、itemsリレーションが設定されていること

- [x]OrderItemModelの実装
  - ファイル: `backend/app/infrastructure/database/models.py`（既存ファイルに追加）
  - 内容: order_itemsテーブル定義、インデックス、CHECK制約、リレーション設定
  - 完了条件: OrderItemModelが定義され、orderリレーションが設定されていること

#### 2.2 リポジトリ実装の作成
- [x]OrderRepositoryの実装
  - ファイル: `backend/app/infrastructure/repositories/order_repository.py`（既存スタブを完全置換）
  - 内容: save、find_by_id、find_by_customer_id、exists_active_order_with_product、_to_entityメソッド実装
  - 依存: OrderModel、OrderItemModel、Order、OrderItem、各値オブジェクト
  - 完了条件: 全メソッドが正しく動作し、エンティティとモデル間の変換が正しく行われること

---

### フェーズ3: 既存コンポーネントの変更

#### 3.1 Stockエンティティへの変更
- [x]allocateメソッドの追加
  - ファイル: `backend/app/domain/stock/entities/stock.py`（既存ファイルに追加）
  - 内容: 在庫引当処理、在庫不足時の例外発生
  - 完了条件: 在庫が正しく減算され、不足時に例外が発生すること

- [x]releaseメソッドの追加
  - ファイル: `backend/app/domain/stock/entities/stock.py`（既存ファイルに追加）
  - 内容: 在庫解放処理
  - 完了条件: 在庫が正しく加算されること

#### 3.2 ProductRepositoryへの変更
- [x]find_by_idsメソッド追加（インターフェース）
  - ファイル: `backend/app/domain/product/repositories/product_repository.py`（既存ファイルに追加）
  - 内容: 複数商品ID一括取得のインターフェース定義
  - 完了条件: メソッドシグネチャが定義されていること

- [x]find_by_idsメソッド追加（実装）
  - ファイル: `backend/app/infrastructure/repositories/product_repository.py`（既存ファイルに追加）
  - 内容: SQLAlchemy 2.0スタイルでIN句を使用した一括取得実装
  - 完了条件: 複数商品が一括で取得でき、削除済み商品が除外されること

---

### フェーズ4: Application層の実装

#### 4.1 DTO定義の作成
- [x]注文DTO群の実装
  - ファイル: `backend/app/application/order/dtos/order_dto.py`
  - 内容: OrderItemInputDTO、CreateOrderInputDTO、OrderItemDTO、ShippingAddressDTO、OrderDTO、OrderStatusUpdateDTO、OrderCancelDTO
  - 完了条件: 全DTOが定義され、OrderDTO.from_entityメソッドが正しく動作すること

- [x]__init__.pyファイルの作成
  - ファイル: `backend/app/application/order/dtos/__init__.py`
  - 内容: 空ファイル
  - 完了条件: ファイルが存在すること

#### 4.2 Application層例外の作成
- [x]注文アプリケーション例外の実装
  - ファイル: `backend/app/application/order/exceptions.py`
  - 内容: OrderApplicationError、CustomerNotFoundError、ProductNotFoundError、InsufficientStockError、InvalidCouponError、InvalidShippingAddressError、OrderNotFoundError、InvalidStatusTransitionError、OrderCannotBeCancelledError
  - 完了条件: 各例外クラスが定義されていること

#### 4.3 ユースケースの作成
- [x]CreateOrderUseCaseの実装
  - ファイル: `backend/app/application/order/usecases/create_order_usecase.py`
  - 内容: 顧客検証、配送先住所検証、商品取得、在庫引当、注文生成、永続化、トランザクション管理
  - 依存: DTO、例外、各リポジトリ、OrderDomainService
  - 完了条件: 注文が正しく作成され、トランザクションが管理されること

- [x]GetOrderUseCaseの実装
  - ファイル: `backend/app/application/order/usecases/get_order_usecase.py`
  - 内容: 注文取得、DTO変換
  - 依存: OrderRepository、OrderDTO、OrderNotFoundError
  - 完了条件: 注文が取得でき、存在しない場合に例外が発生すること

- [x]UpdateOrderStatusUseCaseの実装
  - ファイル: `backend/app/application/order/usecases/update_order_status_usecase.py`
  - 内容: 注文取得、ステータス遷移、永続化、トランザクション管理
  - 依存: OrderRepository、OrderStatusUpdateDTO、例外
  - 完了条件: ステータスが正しく更新され、不正な遷移時に例外が発生すること

- [x]CancelOrderUseCaseの実装
  - ファイル: `backend/app/application/order/usecases/cancel_order_usecase.py`
  - 内容: 注文取得、キャンセル可否判定、在庫解放、永続化、トランザクション管理
  - 依存: OrderRepository、StockRepository、OrderCancelDTO、例外
  - 完了条件: 注文が正しくキャンセルされ、在庫が戻されること

- [x]__init__.pyファイルの作成
  - ファイル: `backend/app/application/order/usecases/__init__.py`
  - 内容: 空ファイル
  - 完了条件: ファイルが存在すること

- [x]__init__.pyファイルの作成
  - ファイル: `backend/app/application/order/__init__.py`
  - 内容: 空ファイル
  - 完了条件: ファイルが存在すること

---

### フェーズ5: Presentation層の実装

#### 5.1 Pydanticスキーマの作成
- [x]注文スキーマ群の実装
  - ファイル: `backend/app/schemas/order.py`
  - 内容: OrderItemRequest、OrderCreateRequest、OrderItemResponse、ShippingAddressResponse、OrderResponse、OrderStatusUpdateRequest、OrderStatusUpdateResponse、OrderCancelRequest、OrderCancelResponse、各種DataResponseラッパー
  - 完了条件: 全スキーマが定義され、バリデーションが正しく動作すること

#### 5.2 FastAPIエンドポイントの作成
- [x]注文エンドポイントの実装
  - ファイル: `backend/app/api/v1/endpoints/orders.py`
  - 内容: POST /（注文作成）、GET /{order_id}（注文詳細取得）、PUT /{order_id}/status（ステータス更新）、POST /{order_id}/cancel（キャンセル）
  - 依存: Pydanticスキーマ、ユースケース、リポジトリ、例外
  - 完了条件: 4つのエンドポイントが正しく動作し、エラーハンドリングが適切に行われること

#### 5.3 ルーティング登録
- [x]APIルーターへの登録
  - ファイル: `backend/app/api/v1/router.py`（既存ファイルに追加）
  - 内容: orders.pyのルーターを `/orders` パスでinclude
  - 完了条件: `/api/v1/orders` 配下のエンドポイントにアクセスできること

---

### フェーズ6: データベースマイグレーション

#### 6.1 マイグレーションファイルの作成
- [ ] Alembicマイグレーションファイル生成
  - コマンド: `alembic revision --autogenerate -m "Add orders and order_items tables"`
  - 内容: ordersテーブル、order_itemsテーブル、インデックス、CHECK制約の作成
  - 完了条件: マイグレーションファイルが生成されること

- [ ] マイグレーション内容の確認
  - 内容: 生成されたマイグレーションファイルを確認し、テーブル定義が正しいか検証
  - 完了条件: テーブル定義、インデックス、制約が設計書通りであること

- [ ] マイグレーション実行
  - コマンド: `alembic upgrade head`
  - 内容: データベースにテーブルを作成
  - 完了条件: ordersテーブルとorder_itemsテーブルが作成されること

---

## 完了条件（全体）

### 機能要件
- [x]POST /api/v1/orders で注文が作成できること
- [x]GET /api/v1/orders/{order_id} で注文詳細が取得できること
- [x]PUT /api/v1/orders/{order_id}/status でステータスが更新できること
- [x]POST /api/v1/orders/{order_id}/cancel で注文がキャンセルできること
- [x]在庫引当処理が正しく動作すること（在庫不足時はエラー）
- [x]割引計算が仕様通りに実行されること（会員ランク→数量→クーポンの順）
- [x]ステータス遷移が仕様に従って制御されること
- [x]キャンセル時に在庫が正しく戻されること

### 品質要件
- [x]DDDレイヤードアーキテクチャに準拠していること
- [x]各層の責務が明確に分離されていること
- [x]トランザクション境界が適切に管理されていること（Application層）
- [x]バリデーションがPresentation層で実行されていること
- [x]ビジネスルールがDomain層に集約されていること

### エラーハンドリング
- [x]CUSTOMER_NOT_FOUND（404）
- [x]PRODUCT_NOT_FOUND（404）
- [x]INSUFFICIENT_STOCK（400）
- [x]INVALID_SHIPPING_ADDRESS（400）
- [x]ORDER_NOT_FOUND（404）
- [x]INVALID_STATUS_TRANSITION（400）
- [x]ORDER_CANNOT_BE_CANCELLED（409）

### テスト
- [ ] Domain層の単体テスト（エンティティ、値オブジェクト、ドメインサービス）
- [ ] Application層の単体テスト（ユースケース）
- [ ] Infrastructure層の統合テスト（リポジトリ）
- [ ] Presentation層の統合テスト（エンドポイント）

---

## 備考

### 実装の進め方
1. 各フェーズを順番に実装すること（依存関係を考慮）
2. 1つのタスクが完了したらチェックボックスを `[x]` にすること
3. テストを書きながら実装を進めること（TDD推奨）
4. コードレビューは各フェーズ完了時に行うこと

### 注意事項
- SQLAlchemy 2.0スタイルを徹底すること（`Mapped`、`mapped_column`、`select()`使用）
- トランザクション管理はApplication層で行うこと
- ドメインイベントの発行は今回の実装に含めるが、購読者は別タスクとする
- クーポン機能は簡易実装とし、詳細なCouponエンティティは別タスクとする
