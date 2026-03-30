# 要求定義: 商品エンドポイント実装

## 概要
OrderHub（注文管理システム）の例示実装として、商品エンドポイントをDDDレイヤードアーキテクチャに基づいて実装する。
商品は他の集約（注文、在庫）の前提となる基盤的なエンティティであり、最初に実装することで以降の開発の土台を構築する。

## 実装する機能
本作業では、以下の4つのエンドポイントを実装する：

### 1. GET /api/v1/products — 商品一覧取得
- クエリパラメータ：`category`（カテゴリフィルタ）、`page`（ページ番号）、`per_page`（1ページあたりの件数）
- カテゴリでのフィルタリングに対応
- ページネーション機能を実装
- 論理削除済み商品は表示しない

### 2. POST /api/v1/products — 商品登録
- 商品情報（名前、SKU、価格、カテゴリ、説明、初期在庫）を受け取る
- SKU重複チェック
- 商品ドメインオブジェクトと在庫ドメインオブジェクトをトランザクション内で生成・永続化
- 値オブジェクトによるバリデーション（SKUフォーマット、価格が0以上）

### 3. PUT /api/v1/products/{product_id} — 商品更新
- 商品情報（名前、価格、カテゴリ、説明）を更新
- 論理削除済み商品は更新不可
- 価格の妥当性を検証

### 4. DELETE /api/v1/products/{product_id} — 商品削除
- 論理削除として実装（`deleted_at`に日時を設定）
- 未完了の注文に含まれる商品は削除不可（`ProductInUseError`）
- 削除チェックはApplication層で実施

## 技術スタック
- **言語**: Python 3.12
- **Webフレームワーク**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **データベース**: PostgreSQL 15
- **バリデーション**: Pydantic v2
- **マイグレーションツール**: Alembic

## アーキテクチャ
DDDレイヤードアーキテクチャに従い、以下の4層で構成する：

### 1. Presentation層（FastAPIルーター）
- HTTPリクエストの受信
- リクエストボディ・パラメータのバリデーション（Pydantic）
- Application層（UseCase）の呼び出し
- DTOのレスポンス変換
- エラーハンドリングとHTTPステータスコードのマッピング

### 2. Application層（UseCase）
- ビジネスユースケースの実行
- トランザクション制御
- ドメイン層のオブジェクトとリポジトリの協調
- DTOへの変換
- 実装するUseCase：
  - `ListProductsUseCase` — 商品一覧取得
  - `RegisterProductUseCase` — 商品登録（商品 + 初期在庫）
  - `UpdateProductUseCase` — 商品更新
  - `DeleteProductUseCase` — 商品削除

### 3. Domain層（エンティティ・値オブジェクト・リポジトリIF）
- **集約ルート**: `Product`
  - ファクトリメソッド: `Product.create(name, sku, price, category, description)`
  - コマンドメソッド: `update(name, price, category, description)`, `delete()`
  - 不変条件: SKUは空でないこと、価格は0以上、論理削除済みは更新不可
- **集約ルート**: `Stock`（商品登録時の初期在庫用）
  - ファクトリメソッド: `Stock.initialize(product_id, quantity)`
- **値オブジェクト**:
  - `ProductId` — UUID文字列、空でないこと
  - `ProductName` — 1文字以上200文字以下
  - `SKU` — 英数字とハイフンのみ、1〜50文字、パターン `^[A-Za-z0-9\-]+$`
  - `Price` — 0以上の整数（円単位）
  - `StockQuantity` — 0以上の整数
- **リポジトリインターフェース**:
  - `ProductRepository` — `find_by_id`, `find_by_sku`, `find_all`, `save`
  - `StockRepository` — `save`
  - `OrderRepository` — `exists_active_order_with_product`（削除チェック用）
- **ドメイン例外**:
  - `InvalidPriceError` — 価格が負の値
  - `InvalidSKUFormatError` — SKUのフォーマットが不正
  - `ProductAlreadyDeletedError` — 論理削除済み商品の更新試行

### 4. Infrastructure層（SQLAlchemy実装）
- リポジトリインターフェースの実装
- SQLAlchemyモデル定義（`products`, `stocks`, `orders`, `order_items`テーブル）
- ORMマッピング（ドメインオブジェクト ↔ SQLAlchemyモデル）
- データベースセッション管理
- トランザクション制御のサポート

## 受け入れ条件

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
- [ ] 各UseCaseに対する統合テストが存在する
- [ ] エラーケースに対するテストが存在する（SKU重複、存在しない商品ID、削除済み商品の更新、使用中商品の削除）
- [ ] APIドキュメント（OpenAPI/Swagger）が自動生成される

## 制約事項

### 技術的制約
- ドメイン層は純粋なPythonクラスで実装し、外部ライブラリへの依存を避ける
- UUIDの生成はドメイン層で実施（Infrastructure層に依存しない）
- トランザクション制御はApplication層で実施（ドメイン層に漏れ出させない）
- ORMマッピングはInfrastructure層で定義（ドメイン層のエンティティはORMを意識しない）

### ビジネスルール制約
- SKUは一意であること（重複不可）
- 価格は0以上であること
- 論理削除済み商品は更新不可
- 未完了注文（`CONFIRMED`, `PAID`, `PREPARING`, `SHIPPED`）に含まれる商品は削除不可

### データベース制約
- `products`テーブルの`sku`カラムにUNIQUE制約
- `products`テーブルの`price`カラムにCHECK制約（`price >= 0`）
- `stocks`テーブルの`product_id`カラムにUNIQUE制約（1商品につき1在庫レコード）
- 論理削除は`deleted_at`カラムで管理（NULLは未削除、日時設定で削除済み）

## 依存関係

### 前提条件
- PostgreSQLデータベースが起動していること
- 以下のテーブルが存在すること（Alembicマイグレーション実行済み）:
  - `products`
  - `stocks`
  - `orders`
  - `order_items`
- FastAPIプロジェクトの基本構成が存在すること

### 他コンポーネントへの依存
- 本実装は他の集約（注文集約、顧客集約）に依存しない
- ただし、商品削除時のチェックで`OrderRepository.exists_active_order_with_product`を使用する
  - このメソッドは本作業でインターフェースのみ定義し、スタブ実装を用意する
  - 注文エンドポイント実装時に実装を完成させる

### 後続の実装への影響
- 商品エンドポイント実装後、以下の実装が可能になる：
  1. 在庫エンドポイント実装（`Stock`集約の完全な実装）
  2. 顧客エンドポイント実装（`Customer`集約の実装）
  3. 注文エンドポイント実装（`Order`集約の実装、商品・在庫との協調）

## 参照ドキュメント
- `docs/ddd/api-design/products.md` — 商品エンドポイントAPI設計書
- `docs/ddd/domain-model-design.md` — ドメインモデル設計書
- `docs/ddd/database-design.md` — データベース設計書
- `docs/ddd/product-requirements.md` — プロダクト要求定義書
