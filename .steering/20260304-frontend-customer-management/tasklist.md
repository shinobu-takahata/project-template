# タスクリスト: フロントエンド 顧客管理機能

## 概要
Next.js App Router で顧客管理機能を実装する。
プロジェクト初期セットアップから始め、型定義・共通基盤・顧客一覧・顧客詳細の順に積み上げる。

---

## タスク一覧

### フェーズ1: Next.js プロジェクト初期セットアップ

- [x] **1.1 Next.js プロジェクト作成**
  - ファイル: `frontend/`
  - 内容: `npx create-next-app@latest` で App Router / TypeScript / Tailwind 有効で作成

- [x] **1.2 shadcn/ui 初期化**
  - ファイル: `frontend/components/ui/`
  - 内容: `npx shadcn@latest init` で初期化し、必要コンポーネントを追加
  - 追加コンポーネント: button, input, label, badge, card, separator, skeleton

- [x] **1.3 追加ライブラリのインストール**
  - 内容: `server-only`, `zod`, `@conform-to/react`, `@conform-to/zod`, `lucide-react`

- [x] **1.4 共通ユーティリティ作成**
  - ファイル: `frontend/lib/utils.ts`
  - 内容: `cn()` ヘルパー（clsx + tailwind-merge）

- [x] **1.5 API クライアント作成**
  - ファイル: `frontend/lib/api-client.ts`
  - 内容: バックエンド API への baseURL・共通ヘッダー・エラーハンドリングを設定した `fetch` ラッパー

---

### フェーズ2: ドメイン型定義

- [x] **2.1 Customer 型定義**
  - ファイル: `frontend/types/customer.ts`
  - 内容: `MemberRank`, `Address`, `ShippingAddress`, `Customer` 型

- [x] **2.2 Order 型定義**
  - ファイル: `frontend/types/order.ts`
  - 内容: `OrderStatus`, `OrderItem`, `Order` 型

---

### フェーズ3: ルートレイアウト・共通 UI

- [x] **3.1 ルートレイアウト**
  - ファイル: `frontend/app/layout.tsx`
  - 内容: HTML ルート・グローバル CSS・フォント設定

- [x] **3.2 ルートエラーページ**
  - ファイル: `frontend/app/error.tsx`
  - 内容: `"use client"` — エラーメッセージ + 再試行ボタン

- [x] **3.3 顧客管理レイアウト**
  - ファイル: `frontend/app/customers/layout.tsx`
  - 内容: ページタイトル・ナビゲーション等の共通レイアウト

---

### フェーズ4: フェッチ層・型・アクション（[customerId]ルート）

- [x] **4.1 フェッチ関数作成**
  - ファイル: `frontend/app/customers/[customerId]/_lib/fetcher.ts`
  - 内容:
    - `import "server-only"`
    - `getCustomer(id)` — `React.cache()` でメモ化
    - `getCustomerOrders(id)` — 注文履歴取得

- [x] **4.2 顧客情報更新 Action**
  - ファイル: `frontend/app/customers/[customerId]/_actions/update-customer.ts`
  - 内容: `"use server"` — zod バリデーション → API PUT → `revalidateTag`

- [x] **4.3 住所追加 Action**
  - ファイル: `frontend/app/customers/[customerId]/_actions/add-address.ts`
  - 内容: `"use server"` — zod バリデーション → API POST → `revalidateTag`

- [x] **4.4 住所更新 Action**
  - ファイル: `frontend/app/customers/[customerId]/_actions/update-address.ts`
  - 内容: `"use server"` — zod バリデーション → API PUT → `revalidateTag`

- [x] **4.5 住所削除 Action**
  - ファイル: `frontend/app/customers/[customerId]/_actions/delete-address.ts`
  - 内容: `"use server"` — API DELETE → `revalidateTag`

---

### フェーズ5: 顧客プロフィールコンポーネント

- [x] **5.1 CustomerProfileContainer**
  - ファイル: `frontend/app/customers/[customerId]/_components/customer-profile/customer-profile-container.tsx`
  - 内容: Server Component — `getCustomer(id)` を呼び `CustomerProfile` に渡す

- [x] **5.2 CustomerProfile（Presentational）**
  - ファイル: `frontend/app/customers/[customerId]/_components/customer-profile/customer-profile.tsx`
  - 内容: 顧客名・メール・会員ランクを表示。編集ボタンで `CustomerEditForm` を開く

- [x] **5.3 CustomerEditForm**
  - ファイル: `frontend/app/customers/[customerId]/_components/customer-profile/customer-edit-form.tsx`
  - 内容: `"use client"` — `useActionState(updateCustomer)` + conform でフォーム実装

---

### フェーズ6: 配送先住所コンポーネント

- [x] **6.1 ShippingAddressListContainer**
  - ファイル: `frontend/app/customers/[customerId]/_components/shipping-addresses/shipping-address-list-container.tsx`
  - 内容: Server Component — `getCustomer(id)` の住所リストを `ShippingAddressList` に渡す

- [x] **6.2 ShippingAddressList（Presentational）**
  - ファイル: `frontend/app/customers/[customerId]/_components/shipping-addresses/shipping-address-list.tsx`
  - 内容: 住所カードのリスト表示 + 「住所を追加」ボタン

- [x] **6.3 ShippingAddressCard（Presentational）**
  - ファイル: `frontend/app/customers/[customerId]/_components/shipping-addresses/shipping-address-card.tsx`
  - 内容: 住所1件の表示（デフォルト住所バッジ・編集・削除ボタン）

- [x] **6.4 ShippingAddressForm**
  - ファイル: `frontend/app/customers/[customerId]/_components/shipping-addresses/shipping-address-form.tsx`
  - 内容: `"use client"` — 追加/編集フォーム。`useActionState(addAddress / updateAddress)` + conform

---

### フェーズ7: 注文履歴コンポーネント

- [x] **7.1 OrderHistoryContainer**
  - ファイル: `frontend/app/customers/[customerId]/_components/order-history/order-history-container.tsx`
  - 内容: Server Component — `getCustomerOrders(id)` → `OrderHistoryList` に渡す

- [x] **7.2 OrderHistoryList（Presentational）**
  - ファイル: `frontend/app/customers/[customerId]/_components/order-history/order-history-list.tsx`
  - 内容: 注文一覧の表示

- [x] **7.3 OrderHistoryItem（Presentational）**
  - ファイル: `frontend/app/customers/[customerId]/_components/order-history/order-history-item.tsx`
  - 内容: 注文1件の表示（注文ID・ステータス・合計金額・日時）

- [x] **7.4 OrderHistorySkeleton**
  - ファイル: `frontend/app/customers/[customerId]/_components/order-history/order-history-skeleton.tsx`
  - 内容: Suspense fallback 用スケルトン UI

---

### フェーズ8: ページ組み立て

- [x] **8.1 顧客詳細ページ**
  - ファイル: `frontend/app/customers/[customerId]/page.tsx`
  - 内容: Server Component — 各 Container を並行レンダリング。OrderHistory は `<Suspense>` でラップ

- [x] **8.2 顧客詳細エラーページ**
  - ファイル: `frontend/app/customers/[customerId]/error.tsx`
  - 内容: `"use client"` — エラーメッセージ + 再試行ボタン

- [x] **8.3 顧客詳細 not-found ページ**
  - ファイル: `frontend/app/customers/[customerId]/not-found.tsx`
  - 内容: 「顧客が見つかりません」メッセージ

- [x] **8.4 顧客詳細ローディングページ**
  - ファイル: `frontend/app/customers/[customerId]/loading.tsx`
  - 内容: ページ全体のスケルトン UI

- [x] **8.5 顧客一覧ページ**
  - ファイル: `frontend/app/customers/page.tsx`
  - 内容: Server Component — 顧客一覧取得・表示、新規登録ボタン

- [x] **8.6 顧客新規登録ページ**
  - ファイル: `frontend/app/customers/new/page.tsx` + `_components/customer-new-form.tsx`
  - 内容: 新規顧客登録フォーム

---

## 完了条件
- [x] すべてのタスクが完了している
- [x] `requirements.md` の受け入れ条件をすべて満たしている
- [x] データフェッチが Client Components で行われていない
- [x] `error.tsx` が `"use client"` になっている
- [x] Server Actions でバリデーションエラーを `throw` していない
- [ ] `frontend/` が `docker-compose.yml` のサービスとして起動できる（任意）
