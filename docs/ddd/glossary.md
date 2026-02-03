# DDD用語集 - 注文管理システム（OrderHub）

## 概要
本ドキュメントでは、DDD（ドメイン駆動設計）の主要な用語と、本プロジェクト（OrderHub）における具体的な適用例を対応づけて説明する。

---

## 戦略的設計の用語

### ドメイン（Domain）
ソフトウェアが解決しようとするビジネス上の問題領域。

**OrderHubでの例:** ECサイトにおける注文管理業務全体。商品の販売、注文の受付・管理、在庫管理、顧客管理を含む。

---

### サブドメイン（Subdomain）
ドメインを構成するより小さな問題領域。コアドメイン・支援ドメイン・汎用ドメインに分類される。

| 分類 | 説明 | OrderHubでの例 |
|------|------|--------------|
| コアドメイン | ビジネスの競争優位性を生む中核領域 | 注文管理、割引計算 |
| 支援ドメイン | コアドメインを支える領域 | 在庫管理、顧客管理 |
| 汎用ドメイン | どのビジネスでも共通する領域 | 認証、メール送信（本PJではスコープ外） |

---

### 境界づけられたコンテキスト（Bounded Context）
特定のドメインモデルが一貫して適用される範囲。同じ用語でもコンテキストが異なれば意味が変わる。

**OrderHubでの例:** 本プロジェクトは単一の「注文管理コンテキスト」として構成している。実際の大規模システムでは「受注コンテキスト」「出荷コンテキスト」「請求コンテキスト」のように分割される。

---

### ユビキタス言語（Ubiquitous Language）
開発チームとドメインエキスパートが共通して使う用語。コード・ドキュメント・会話すべてで同じ言葉を使う。

**OrderHubでの例:**

| ユビキタス言語 | コード上の表現 | 意味 |
|-------------|-------------|------|
| 注文 | `Order` | 顧客が商品を購入する行為とその記録 |
| 注文明細 | `OrderItem` | 注文に含まれる個々の商品と数量 |
| 注文確定 | `OrderStatus.CONFIRMED` | 注文が受け付けられた状態 |
| 在庫引当 | `Stock.allocate()` | 注文に対して在庫を確保すること |
| 在庫戻し | `Stock.release()` | キャンセルにより引当済み在庫を解放すること |
| 会員ランク | `MemberRank` | 顧客の購入実績に基づくランク（ブロンズ/シルバー/ゴールド） |
| クーポン適用 | `DiscountPolicy.calculate()` | 割引クーポンを注文に適用すること |
| 論理削除 | `Product.delete()` | データを物理的に消さず、削除済みとしてマークすること |

---

### コンテキストマップ（Context Map）
複数の境界づけられたコンテキスト間の関係を示す図。

**OrderHubでの例:** 単一コンテキストのため本PJでは扱わない。実務では「注文コンテキストが決済コンテキストを呼び出す」といった関係をマッピングする。

---

## 戦術的設計の用語

### エンティティ（Entity）
一意の識別子（ID）を持ち、ライフサイクルを通じて同一性が保たれるオブジェクト。属性が変わってもIDが同じなら同じオブジェクトとみなす。

**OrderHubでの例:**
| エンティティ | 識別子 | 説明 |
|------------|-------|------|
| `Order` | `OrderId` | 注文。ステータスが変わっても同じ注文 |
| `OrderItem` | `OrderItemId` | 注文明細。Order集約内のエンティティ |
| `Product` | `ProductId` | 商品。価格が変わっても同じ商品 |
| `Stock` | `StockId` | 在庫。数量が変わっても同じ在庫レコード |
| `Customer` | `CustomerId` | 顧客。名前が変わっても同じ顧客 |
| `ShippingAddress` | `id` | 配送先住所。Customer集約内のエンティティ |

---

### 値オブジェクト（Value Object）
識別子を持たず、属性の値そのものが意味を持つオブジェクト。不変（イミュータブル）であり、等価性は全属性の一致で判定する。

**OrderHubでの例:**
| 値オブジェクト | 保持する値 | なぜ値オブジェクトか |
|-------------|----------|-----------------|
| `Money` | `amount: int` | 金額の計算ルール（加減算、端数処理）をカプセル化 |
| `OrderStatus` | `value: str` | 遷移ルールをカプセル化。`"CONFIRMED"` という文字列以上の意味を持つ |
| `MemberRank` | `value: str` | 割引率のマッピングをカプセル化 |
| `Address` | postal_code, prefecture, city, street | 住所のフォーマット検証をカプセル化 |
| `SKU` | `value: str` | フォーマットルール（英数字+ハイフン）をカプセル化 |
| `Quantity` | `value: int` | 「0より大きい」という制約をカプセル化 |

**値オブジェクトにする判断基準:**
- そのデータに独自のバリデーションルールがあるか？ → あれば値オブジェクト
- そのデータに振る舞い（計算ロジック等）があるか？ → あれば値オブジェクト
- 複数の箇所で同じ制約を繰り返し書くことになるか？ → なるなら値オブジェクト

---

### 集約（Aggregate）
関連するエンティティと値オブジェクトのまとまり。データの整合性を保つ単位であり、トランザクション境界でもある。外部からは集約ルート経由でのみアクセスする。

**OrderHubでの例:**

```
┌─────────────────────────────────┐
│ Order集約                        │
│                                 │
│  Order (集約ルート)               │
│   ├── OrderItem (エンティティ)     │
│   ├── OrderItem (エンティティ)     │
│   ├── Money (値オブジェクト)       │
│   └── OrderStatus (値オブジェクト) │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Customer集約                     │
│                                 │
│  Customer (集約ルート)            │
│   ├── ShippingAddress (エンティティ)│
│   ├── ShippingAddress (エンティティ)│
│   ├── MemberRank (値オブジェクト)  │
│   └── EmailAddress (値オブジェクト)│
└─────────────────────────────────┘
```

---

### 集約ルート（Aggregate Root）
集約の入り口となるエンティティ。外部から集約内のオブジェクトを操作するには、必ず集約ルートを経由する。

**OrderHubでの例:**
```python
# 正しい: 集約ルート経由で操作
order.cancel(reason="注文間違い")

# 誤り: 集約内のエンティティを直接操作
order.items[0].quantity = 5  # 集約の不変条件が破壊される可能性
```

**なぜ集約ルート経由にするのか:**
- 集約の不変条件（例: 合計金額の整合性）を集約ルートが保証するため
- 集約内のエンティティを直接変更すると、不変条件のチェックをバイパスしてしまう

---

### 不変条件（Invariant）
集約が常に満たすべきビジネスルール。集約ルートのメソッドがこれを保証する。

**OrderHubでの例:**
| 集約 | 不変条件 |
|------|---------|
| Order | 注文明細は1件以上 |
| Order | 合計金額 >= 0 |
| Order | ステータス遷移は定義されたもののみ |
| Stock | allocated_quantity <= quantity |
| Customer | 配送先住所は最大5件 |
| Customer | デフォルト住所は1件のみ |

---

### ドメインサービス（Domain Service）
特定のエンティティや値オブジェクトに属さないドメインロジック。複数の集約をまたぐ操作や、単一の集約に置くと不自然なロジックを担当する。

**OrderHubでの例:**
| ドメインサービス | 理由 |
|---------------|------|
| `OrderDomainService` | 注文作成時に Order集約と Stock集約の両方を操作する必要がある |
| `DiscountPolicy` | 割引計算は Order でも Customer でもなく、複数の情報を横断して算出する |
| `TaxCalculator` | 税計算はどの集約にも属さない汎用的な計算ロジック |

**注意:** ドメインサービスを安易に使うとドメインモデルが貧血モデル（Anemic Domain Model）になる。まず集約に置けないか検討し、複数集約の協調が必要な場合にのみ使う。

---

### ドメインイベント（Domain Event）
ドメインで発生した重要な出来事を表すオブジェクト。過去形で命名する。

**OrderHubでの例:**
| イベント | 発生タイミング | 目的 |
|---------|-------------|------|
| `OrderPlaced` | 注文作成時 | 後続処理（通知等）のトリガー |
| `OrderCancelled` | 注文キャンセル時 | 返金処理等のトリガー |
| `LowStockDetected` | 在庫が閾値以下 | 発注アラートのトリガー |

**イベントの特徴:**
- 不変（イミュータブル）: 過去に起きたことは変更できない
- 過去形で命名: `OrderPlaced`（注文が確定された）
- ペイロードは自己完結: イベント単体で意味が伝わるデータを持つ

---

### リポジトリ（Repository）
集約の永続化と復元を担当するインターフェース。ドメイン層にインターフェースを定義し、Infrastructure層で実装する。

**OrderHubでの例:**
```python
# Domain層: インターフェース定義（抽象クラス）
class OrderRepository(ABC):
    def find_by_id(self, order_id: OrderId) -> Optional[Order]: ...
    def save(self, order: Order) -> None: ...

# Infrastructure層: 具体的な実装
class SqlAlchemyOrderRepository(OrderRepository):
    def find_by_id(self, order_id: OrderId) -> Optional[Order]:
        # SQLAlchemyでDBからデータ取得し、ドメインオブジェクトに変換
        ...
```

**ポイント:**
- リポジトリは集約単位で作る（OrderItemRepository は作らない）
- ドメイン層はDBの存在を知らない
- コレクションのように振る舞う（`find`, `save`）

---

### ファクトリ（Factory）
複雑なオブジェクトの生成ロジックをカプセル化するパターン。

**OrderHubでの例:** 集約ルートの静的ファクトリメソッドとして実装する。
```python
class Order:
    @staticmethod
    def create(customer_id, items, shipping_address, ...) -> "Order":
        # ID採番、初期ステータス設定、金額計算、イベント記録
        # → コンストラクタに生の引数を渡すより意図が明確
```

---

## アーキテクチャの用語

### レイヤードアーキテクチャ（Layered Architecture）
アプリケーションを複数の層に分割し、各層の責務を明確にする設計パターン。

**OrderHubでの4層構成:**

| 層 | 責務 | OrderHubでの実装 |
|----|------|----------------|
| Presentation層 | HTTPリクエスト/レスポンスの処理 | FastAPI Router, Pydanticスキーマ |
| Application層 | ユースケースの実行、トランザクション制御 | UseCase クラス |
| Domain層 | ビジネスロジック | Entity, ValueObject, DomainService, Repository IF |
| Infrastructure層 | 技術的な実装詳細 | SQLAlchemy Repository実装, イベントバス |

---

### 依存性逆転の原則（Dependency Inversion Principle）
上位モジュールが下位モジュールの具体的な実装に依存するのではなく、抽象（インターフェース）に依存するようにする原則。

**OrderHubでの例:**
```
Domain層: OrderRepository (抽象クラス)    ← 定義
    ↑
Infrastructure層: SqlAlchemyOrderRepository  ← 実装

Application層: CreateOrderUseCase
    → OrderRepository (抽象) に依存  ← 具体実装を知らない
```

**メリット:** ドメイン層がSQLAlchemyやDBの詳細を知らずに済む。テスト時にインメモリ実装に差し替えることも容易。

---

### DTO（Data Transfer Object）
層間でデータを受け渡すためのオブジェクト。ドメインオブジェクトを外部に公開せず、必要なデータだけを含む。

**OrderHubでの例:**
- Application層 → Presentation層: `OrderDTO`（ドメインオブジェクトの情報をフラットに変換）
- Presentation層 → Application層: `CreateOrderRequest`（Pydanticスキーマ）

---

### 貧血ドメインモデル（Anemic Domain Model）
エンティティがデータの入れ物に過ぎず、ビジネスロジックがすべてサービス層にある状態。DDDのアンチパターン。

**悪い例（貧血モデル）:**
```python
class Order:
    status: str  # ただのデータ

class OrderService:
    def cancel(self, order):
        if order.status in ("SHIPPED", "DELIVERED"):
            raise Error  # ロジックがサービスに漏れている
        order.status = "CANCELLED"
```

**良い例（リッチドメインモデル）:**
```python
class Order:
    def cancel(self, reason: str) -> None:
        if not self.status.is_cancellable:
            raise OrderCannotBeCancelledError
        self._status = OrderStatus.CANCELLED
        self._cancel_reason = reason
        self._add_event(OrderCancelled(...))
```

---

### 楽観的ロック（Optimistic Lock）
データ更新時にバージョン番号を確認し、競合を検出する排他制御方式。

**OrderHubでの例:** `Stock` 集約の `version` カラム。同時に複数の注文が同じ商品の在庫を引当てようとした場合、先に更新した方が成功し、後から更新しようとした方は `OptimisticLockError` となりリトライする。

---

### Outboxパターン
ドメインイベントをトランザクション内でDBに保存し、後から非同期で発行するパターン。イベントの確実な配信を保証する。

**OrderHubでの例:** `domain_events` テーブルに保存。本PJではOutbox保存までを実装し、非同期コンシューマは実装しない。

---

## よくある疑問

### Q: エンティティと値オブジェクトの違いは？
- **エンティティ**: IDで識別する。「田中太郎さん（ID: cust-001）が名前を変えても同じ顧客」
- **値オブジェクト**: 値で識別する。「1,000円は1,000円。どの1,000円かは区別しない」

### Q: ドメインサービスとApplication層のユースケースの違いは？
- **ドメインサービス**: 純粋なビジネスロジック。DBやHTTPを知らない。例: 割引計算
- **ユースケース**: ドメインオブジェクトの協調、トランザクション制御、リポジトリ呼び出し。例: 注文作成の一連のフロー

### Q: 集約の境界はどう決める？
- トランザクション整合性が必要な範囲をひとつの集約にする
- 小さく保つ。迷ったら分割する
- 例: OrderとStockは別集約。注文と在庫を同一トランザクションで更新する必要はあるが、それはApplication層で制御する

### Q: 値オブジェクトにすべきかプリミティブ型のままでよいか？
- バリデーションや計算ロジックがあるなら値オブジェクト（例: Money, SKU）
- 単なるラベルで特別なルールがないなら文字列のまま（例: category, description）
