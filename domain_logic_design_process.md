# ドメインロジック設計の進め方

## 概要

ビジネスロジックをどこに書くかを決める際の設計順序をまとめたドキュメント。
基本方針は「**残りもの思考**」— エンティティ・VOに持たせられるものを先に吸収し、残ったものをサービス・ポリシーに回す。

---

## 設計の全体フロー

```
① エンティティ・VOの抽出
        ↓
② ドメインロジックの配置先を決める
        ↓
③ 残ったロジックをサービス・ポリシーへ
```

---

## STEP 1：エンティティ・バリューオブジェクトの抽出

業務フロー・要件定義書・既存資料から、ドメインの概念を洗い出す。

### エンティティの見つけ方

- **同一性（ID）で区別されるもの**　→ エンティティ
  - 例：注文、ユーザー、商品
- **ライフサイクルがあるもの**（作成 → 更新 → 削除）　→ エンティティ
- **ステータスが変化するもの**　→ エンティティ（ステータス遷移図を書く）

### バリューオブジェクト（VO）の見つけ方

- **値そのものが同一性を持つもの**　→ VO
  - 例：金額（Money）、住所、メールアドレス、期間
- **値と一緒にルールが移動するもの**　→ VO
  - 例：`Money` が通貨換算ルールを持つ、`Email` がフォーマット検証を持つ
- **不変（イミュータブル）なもの**　→ VO

### チェックポイント

```
「このデータ、IDがなくても成立する？」　→ YES なら VO 候補
「この値、単体で意味を持つルールがある？」　→ YES なら VO 候補
```

---

## STEP 2：ドメインロジックの配置先を決める

抽出した概念に対して、業務フローや仕様書から「計算」「制約」「分岐」を探し、以下の基準で配置先を決める。

### 配置先の判断基準

| ロジックの性質 | 配置先 | 例 |
|---|---|---|
| 単一VOの中で完結する計算・検証 | **VO** | `Money.add()`, `Email.isValid()` |
| 単一エンティティの状態変化・制約 | **エンティティのメソッド** | `Order.cancel()`, `Order.canShip()` |
| 複数エンティティをまたぐ**ドメインルール**（業務上の名前がつく） | **ドメインサービス** | `TransferDomainService`（振替ルール） |
| 複数エンティティをまたぐ**ユースケースの調整**（リポジトリを使う） | **アプリケーションサービス** | `OrderApplicationService`（注文確定のフロー全体） |
| 複数ルールの組み合わせ・増減がある判定 | **ポリシークラス** | 送料無料条件、割引適用判定 |

### 判断フロー

```
ロジックを見つけたら...

1. 単一のVO・エンティティに閉じているか？
   → YES：そのクラスのメソッドとして持たせる

2. 複数エンティティをまたぐか？
   → YES：そのルール自体に業務上の名前がつくか？
       → YES かつ リポジトリ不要：ドメインサービスへ
       → リポジトリが必要 / ユースケースの調整：アプリケーションサービスへ

3. ルールが複数あって増減する可能性があるか？
   → YES：ポリシークラスへ

4. シンプルな単一チェック・計算か？
   → YES：関数で十分（クラスにしない）
```

---

## STEP 3：各配置先の責務と設計ポイント

### バリューオブジェクト（VO）

**責務**：値の保持 ＋ 値に紐づくルールの表現

```python
class Money:
    def __init__(self, amount: int, currency: str):
        if amount < 0:
            raise ValueError("金額は0以上である必要があります")
        self.amount = amount
        self.currency = currency

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("通貨が異なります")
        return Money(self.amount + other.amount, self.currency)
```

**設計ポイント**
- イミュータブルにする（操作は新しいインスタンスを返す）
- バリデーションはコンストラクタで行う
- VOを先に疑う：エンティティのメソッドにしようとしているロジックが、実はVOに持たせられることが多い

---

### エンティティ

**責務**：同一性の管理 ＋ 状態遷移ルールの表現

```python
class Order:
    def cancel(self):
        if self.status != OrderStatus.PENDING:
            raise DomainException("未確定の注文のみキャンセル可能です")
        self.status = OrderStatus.CANCELLED

    def can_ship(self) -> bool:
        return self.status == OrderStatus.CONFIRMED and self.payment_confirmed
```

**設計ポイント**
- ステータス遷移図を先に書く → 遷移条件がそのままメソッドの制約になる
- `can_xxx()` で事前条件チェックを公開しておくとサービス層が使いやすい

---

### ドメインサービス

**責務**：複数エンティティをまたぐ、ドメインルールとして名前がつく概念の表現

使うべき条件は以下の3つ。

- 複数エンティティをまたぐロジックである
- そのルール自体に業務上の名前がつく（例：「振替」「予約可否判定」）
- リポジトリを呼び出さずに完結する

```python
# 「口座振替」は BankAccount 単体では表現できないが、ドメインルールとして名前がつく
class TransferDomainService:
    def transfer(self, from_account: BankAccount, to_account: BankAccount, amount: Money):
        if not from_account.can_withdraw(amount):
            raise DomainException("残高不足")
        if to_account.is_frozen():
            raise DomainException("振込先口座が凍結されています")
        from_account.withdraw(amount)
        to_account.deposit(amount)
```

**使わなくていいサイン**
- ロジックが1つのエンティティに閉じている → エンティティのメソッドで十分
- リポジトリを呼び出している → それはアプリケーションサービスの仕事
- ルールに業務上の名前がつかない → 単なる手続きの寄せ集めになっている可能性が高い

---

### アプリケーションサービス

**責務**：ユースケースのオーケストレーション（リポジトリ・ドメインサービス・外部サービスの調整）

```python
class OrderApplicationService:
    def place_order(self, user_id: str, cart: Cart) -> Order:
        # リポジトリからエンティティを取得
        for item in cart.items:
            inventory = self.inventory_repo.find(item.product_id)
            inventory.reserve(item.quantity)  # 制約はInventory側が持つ

        # 注文生成（Orderエンティティ）
        order = Order.create(user_id, cart)
        self.order_repo.save(order)
        return order
```

**設計ポイント**
- ロジックを「持たない」。エンティティ・ドメインサービスへの委譲に徹する
- ロジックをここに書きたくなったら、エンティティ・VOに移せるサインかもしれない
- 「置き場に迷ったもの」の墓場にしない

---

### ポリシークラス

**責務**：複数ルールの組み合わせ・切り替えが必要な判定

```python
class FreeShippingPolicy:
    def is_satisfied_by(self, order: Order) -> bool:
        return order.total >= Money(3000, "JPY") and not order.has_frozen_items

class GoldMemberFreeShippingPolicy:
    def is_satisfied_by(self, order: Order) -> bool:
        return order.user.rank == UserRank.GOLD and not order.has_frozen_items

class ShippingCalculator:
    def __init__(self, policies: list):
        self.policies = policies

    def calculate(self, order: Order) -> Money:
        for policy in self.policies:
            if policy.is_satisfied_by(order):
                return Money(0, "JPY")
        return Money(800, "JPY") if order.has_frozen_items else Money(500, "JPY")
```

**ポリシークラスを使う判断基準**

```
「このルールに業務上の名前がつけられるか？」
「このルールは将来、追加・変更・削除される可能性があるか？」

→ 両方 YES ならポリシークラスにする価値がある
```

**使わなくていいケース**
- ルールが1つだけ → 関数で十分
- 条件がシンプルな単一チェック → エンティティのメソッドで十分
- 計算・変換がメイン → Calculator / Strategy パターンの方が自然

---

## まとめ：配置先の一覧

| 配置先 | 向いているロジック | アンチパターン |
|---|---|---|
| **VO** | 値に紐づく計算・検証 | ステートフルな処理 |
| **エンティティ** | 状態遷移・単一オブジェクト内の制約 | 他エンティティへの依存 |
| **ドメインサービス** | 複数エンティティをまたぐドメインルール（業務上の名前がつく・リポジトリ不要） | リポジトリを使う処理、名前のない手続き |
| **アプリケーションサービス** | ユースケースのオーケストレーション（リポジトリ・外部サービスとの調整） | ロジックの詰め込み |
| **ポリシー** | 複数ルールの組み合わせ・増減 | ルールが1つだけのケース |
| **関数** | シンプルな単一チェック・変換 | — |

---

## 補足：ロジック洗い出しのインプット

設計の前段として、以下のインプットからビジネスロジックを洗い出す。

- **業務フロー図・シーケンス図**：分岐・計算・制約が発生している箇所を探す
- **要件定義書**：「承認する」「計算する」などの動詞、「〜できない」「〜しなければならない」などの制約表現
- **ステータス遷移図**：エンティティの状態遷移条件 = ビジネスロジック
- **業務担当者へのヒアリング**：異常系・例外ケースを重点的に掘り起こす
- **既存システム・Excel**：リプレース案件では IF ネストや関数の中にロジックが埋まっている
