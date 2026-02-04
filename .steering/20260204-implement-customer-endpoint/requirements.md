# 要求定義: 顧客エンドポイント実装

## 概要
OrderHub（注文管理システム）の例示実装として、顧客エンドポイントをDDDレイヤードアーキテクチャに基づいて実装する。
顧客は注文の主体となる集約であり、配送先住所を集約内エンティティとして管理する。既に実装済みの商品エンドポイントと同じアーキテクチャパターンに従い、4層構造（Presentation / Application / Domain / Infrastructure）で実装する。

## 実装する機能
本作業では、以下の5つのエンドポイントを実装する：

### 1. GET /api/v1/customers/{customer_id} — 顧客情報取得
- パスパラメータ：`customer_id`（顧客ID）
- 顧客の基本情報（名前、メールアドレス、会員ランク、作成日時）を返却
- 配送先住所一覧を含む（Eager Loading）
- 論理削除は行わないため、削除フィルタは不要

### 2. POST /api/v1/customers — 顧客登録
- 顧客情報（名前、メールアドレス、初期配送先住所）を受け取る
- メールアドレス重複チェック
- 会員ランクは初期値BRONZEで登録
- 初期配送先住所を同時に登録（デフォルトフラグ: true）
- 値オブジェクトによるバリデーション（メールアドレスフォーマット、郵便番号フォーマット）

### 3. PUT /api/v1/customers/{customer_id} — 顧客情報更新
- 顧客情報（名前、メールアドレス）を更新
- メールアドレス変更時は重複チェック
- 配送先住所の更新は別エンドポイントで実施（このエンドポイントでは対象外）

### 4. POST /api/v1/customers/{customer_id}/addresses — 配送先住所追加
- 顧客に新しい配送先住所を追加
- 最大5件までの制約をドメイン層で実施
- `is_default=true` の場合、既存のデフォルト住所を解除
- 住所のバリデーション（郵便番号フォーマット：NNN-NNNN）

### 5. GET /api/v1/customers/{customer_id}/orders — 顧客注文履歴取得
- 指定顧客の注文履歴を取得
- クエリパラメータ：`status`（ステータスでフィルタ）、`page`（ページ番号）、`per_page`（1ページあたりの件数）
- ページネーション機能を実装
- 注文エンドポイントが未実装のため、今回は空のリストを返すスタブ実装とする

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
  - `GetCustomerUseCase` — 顧客情報取得
  - `RegisterCustomerUseCase` — 顧客登録（顧客 + 初期配送先住所）
  - `UpdateCustomerUseCase` — 顧客情報更新
  - `AddShippingAddressUseCase` — 配送先住所追加
  - `ListCustomerOrdersUseCase` — 顧客注文履歴取得（スタブ実装）

### 3. Domain層（エンティティ・値オブジェクト・リポジトリIF）
- **集約ルート**: `Customer`
  - ファクトリメソッド: `Customer.create(name, email)`
  - コマンドメソッド: `update(name, email)`, `add_shipping_address(address)`, `get_shipping_address(address_id)`
  - 不変条件: 配送先住所は最大5件、デフォルト住所は常に1件のみ
- **集約内エンティティ**: `ShippingAddress`
  - 顧客集約内で管理され、Customer経由でのみアクセス可能
- **値オブジェクト**:
  - `CustomerId` — UUID文字列、空でないこと
  - `CustomerName` — 1文字以上100文字以下
  - `EmailAddress` — RFC準拠のメールアドレスフォーマット
  - `MemberRank` — BRONZE / SILVER / GOLD の列挙型
  - `Address` — 郵便番号（NNN-NNNN）、都道府県、市区町村、番地
- **リポジトリインターフェース**:
  - `CustomerRepository` — `find_by_id`, `find_by_email`, `save`
  - `OrderRepository` — `find_by_customer_id`（スタブ実装用）
- **ドメイン例外**:
  - `MaxAddressLimitExceededError` — 配送先住所が5件を超過
  - `ShippingAddressNotFoundError` — 指定IDの住所が存在しない
  - `InvalidEmailFormatError` — メールアドレスフォーマット不正
  - `InvalidPostalCodeFormatError` — 郵便番号フォーマット不正

### 4. Infrastructure層（SQLAlchemy実装）
- リポジトリインターフェースの実装
- SQLAlchemyモデル定義（`customers`, `shipping_addresses`テーブル）
- ORMマッピング（ドメインオブジェクト ↔ SQLAlchemyモデル）
- データベースセッション管理
- トランザクション制御のサポート

## 受け入れ条件

### 機能要件
- [ ] GET /api/v1/customers/{customer_id} が顧客情報と配送先住所一覧を返却する
- [ ] POST /api/v1/customers がメールアドレス重複時に適切なエラー（`DUPLICATE_EMAIL`）を返す
- [ ] POST /api/v1/customers が顧客と初期配送先住所をトランザクション内で作成する
- [ ] POST /api/v1/customers が会員ランクBRONZEで顧客を登録する
- [ ] PUT /api/v1/customers/{customer_id} が存在しない顧客IDに対して`CUSTOMER_NOT_FOUND`を返す
- [ ] PUT /api/v1/customers/{customer_id} がメールアドレス変更時に重複チェックを実施する
- [ ] POST /api/v1/customers/{customer_id}/addresses が配送先住所を5件まで追加できる
- [ ] POST /api/v1/customers/{customer_id}/addresses が5件を超える追加時に`MAX_ADDRESS_LIMIT`エラーを返す
- [ ] POST /api/v1/customers/{customer_id}/addresses が`is_default=true`時に既存デフォルトを解除する
- [ ] GET /api/v1/customers/{customer_id}/orders が顧客の存在確認を実施し、スタブとして空リストを返す

### アーキテクチャ要件
- [ ] ドメイン層が外部ライブラリ（FastAPI、SQLAlchemy等）に依存していない
- [ ] ビジネスロジック（メールアドレス検証、郵便番号検証、配送先住所数制限、デフォルト住所管理）がドメイン層に集約されている
- [ ] リポジトリパターンでデータアクセスが抽象化されている
- [ ] Application層がトランザクション境界を制御している
- [ ] 値オブジェクトが不変であり、バリデーションをコンストラクタで実施している
- [ ] ShippingAddressが集約内エンティティとして適切に管理されている（独自リポジトリを持たない）

### 品質要件
- [ ] ドメイン層の単体テストカバレッジが80%以上
- [ ] 各UseCaseに対する統合テストが存在する
- [ ] エラーケースに対するテストが存在する（メールアドレス重複、存在しない顧客ID、配送先住所上限超過、不正なメールアドレス/郵便番号フォーマット）
- [ ] APIドキュメント（OpenAPI/Swagger）が自動生成される

## 制約事項

### 技術的制約
- ドメイン層は純粋なPythonクラスで実装し、外部ライブラリへの依存を避ける
- UUIDの生成はドメイン層で実施（Infrastructure層に依存しない）
- トランザクション制御はApplication層で実施（ドメイン層に漏れ出させない）
- ORMマッピングはInfrastructure層で定義（ドメイン層のエンティティはORMを意識しない）

### ビジネスルール制約
- メールアドレスは一意であること（重複不可）
- 顧客登録時の会員ランクは必ずBRONZE
- 配送先住所は最大5件まで
- デフォルト配送先住所は常に1件のみ（複数のデフォルトは許可しない）
- 郵便番号は「NNN-NNNN」形式（例: 100-0001）
- メールアドレスはRFC準拠のフォーマット

### データベース制約
- `customers`テーブルの`email`カラムにUNIQUE制約
- `shipping_addresses`テーブルは`customers`テーブルに外部キー参照
- `member_rank`はCHECK制約で'BRONZE', 'SILVER', 'GOLD'のみ許可
- 配送先住所の5件制限はアプリケーション層で制御（DB制約では実装しない）

## 依存関係

### 前提条件
- PostgreSQLデータベースが起動していること
- 以下のテーブルが存在すること（Alembicマイグレーション実行済み）:
  - `customers`
  - `shipping_addresses`
- FastAPIプロジェクトの基本構成が存在すること

### 他コンポーネントへの依存
- 本実装は商品集約、在庫集約に依存しない
- 注文履歴取得エンドポイントでは`OrderRepository.find_by_customer_id()`を使用する
  - このメソッドは本作業でインターフェースのみ定義し、スタブ実装を用意する
  - 注文エンドポイント実装時に実装を完成させる

### 後続の実装への影響
- 顧客エンドポイント実装後、以下の実装が可能になる：
  1. 注文エンドポイント実装（`Order`集約の実装、顧客・商品・在庫との協調）
  2. `OrderRepository.find_by_customer_id()`の完全実装
  3. 会員ランクの変更機能（注文金額に応じたランクアップ等）

## 参照ドキュメント
- `docs/ddd/api-design/customers.md` — 顧客エンドポイントAPI設計書
- `docs/ddd/domain-model-design.md` — ドメインモデル設計書
- `docs/ddd/database-design.md` — データベース設計書
- `docs/ddd/api-design/common.md` — 共通API仕様
- `.steering/20260203-implement-product-endpoint/requirements.md` — 商品エンドポイント要求定義（参考）
- `.steering/20260203-implement-product-endpoint/design.md` — 商品エンドポイント設計書（参考）
