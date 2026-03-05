# 設計: フロントエンド 顧客管理機能

## 実装アプローチ

### 基本方針
- **Next.js App Router v15** + **React 19** を使用
- Server Components をデフォルトとし、インタラクションが必要な末端のみ Client Components にする
- データフェッチは各コンポーネントにコロケーション（`_lib/fetcher.ts` 経由）
- ミューテーションは Server Actions（`_actions/`）で実装、バリデーションは `zod` + `@conform-to/zod` で戻り値表現
- UIコンポーネントは `shadcn/ui` を採用（Tailwind CSS ベース）

### コンポーネント分類

| 種別 | 役割 | 例 |
|---|---|---|
| Server Components（Container） | データフェッチ担当 | `customer-profile-container.tsx` |
| Shared Components（Presentational） | 表示のみ・テスト可能 | `customer-profile.tsx` |
| Client Components | フォーム・インタラクション | `shipping-address-form.tsx` |
| Server Actions | ミューテーション | `_actions/update-customer.ts` |

---

## ディレクトリ構成

```
frontend/
├── app/
│   ├── layout.tsx                            # ルートレイアウト
│   ├── page.tsx                              # トップ（/customers へリダイレクト）
│   ├── error.tsx                             # (Client Component)
│   ├── not-found.tsx
│   │
│   └── customers/
│       ├── layout.tsx                        # サイドナビ等の共通レイアウト
│       ├── page.tsx                          # 顧客一覧（Server Component）
│       ├── loading.tsx                       # 一覧スケルトン
│       ├── error.tsx                         # (Client Component)
│       │
│       ├── new/
│       │   ├── page.tsx                      # 新規登録フォームページ
│       │   └── _components/
│       │       └── customer-new-form.tsx     # (Client Component)
│       │
│       └── [customerId]/
│           ├── page.tsx                      # 顧客詳細（Server Component）
│           ├── loading.tsx
│           ├── error.tsx                     # (Client Component)
│           ├── not-found.tsx
│           │
│           ├── _lib/
│           │   └── fetcher.ts                # server-only。getCustomer / getCustomerOrders
│           │
│           ├── _actions/
│           │   ├── update-customer.ts        # 顧客情報更新
│           │   ├── add-address.ts            # 住所追加
│           │   ├── update-address.ts         # 住所更新
│           │   └── delete-address.ts         # 住所削除
│           │
│           └── _components/
│               ├── customer-profile/
│               │   ├── customer-profile-container.tsx    # Server Component
│               │   ├── customer-profile.tsx              # Presentational (Shared)
│               │   └── customer-edit-form.tsx            # (Client Component)
│               │
│               ├── shipping-addresses/
│               │   ├── shipping-address-list-container.tsx  # Server Component
│               │   ├── shipping-address-list.tsx            # Presentational (Shared)
│               │   ├── shipping-address-card.tsx            # Presentational (Shared)
│               │   └── shipping-address-form.tsx            # (Client Component)
│               │
│               └── order-history/
│                   ├── order-history-container.tsx      # Server Component (Suspense対象)
│                   ├── order-history-list.tsx           # Presentational (Shared)
│                   ├── order-history-item.tsx           # Presentational (Shared)
│                   └── order-history-skeleton.tsx       # Suspense fallback
│
├── components/
│   └── ui/                                   # shadcn/ui コンポーネント
│       ├── button.tsx
│       ├── input.tsx
│       ├── label.tsx
│       ├── badge.tsx
│       ├── card.tsx
│       ├── separator.tsx
│       └── skeleton.tsx
│
├── lib/
│   ├── api-client.ts                         # バックエンドAPIへのベースfetch設定
│   └── utils.ts                              # cn() ヘルパー (clsx + tailwind-merge)
│
└── types/
    ├── customer.ts                           # Customer, ShippingAddress, MemberRank 等
    └── order.ts                              # Order, OrderItem, OrderStatus 等
```

---

## データフロー設計

### 顧客詳細ページ（読み取り）

```
page.tsx (Server Component)
├── CustomerProfileContainer     → fetcher.getCustomer(id)     → API GET /customers/{id}
├── ShippingAddressListContainer → fetcher.getCustomer(id)     → Request Memoization で共有
└── <Suspense>
    └── OrderHistoryContainer    → fetcher.getCustomerOrders(id) → API GET /customers/{id}/orders
```

- `getCustomer` は `React.cache()` でメモ化 → Profile と Address が同じデータを共有
- 注文履歴は独立して重いため `<Suspense>` でストリーミング

### 顧客情報更新（書き込み）

```
customer-edit-form.tsx (Client Component)
└── useActionState(updateCustomer, initialState)
    └── _actions/update-customer.ts ("use server")
        ├── zod バリデーション → エラーは戻り値で返す（throwしない）
        ├── API PUT /customers/{id}
        └── revalidateTag("customer-{id}") → キャッシュ更新
```

### 配送先住所管理

```
shipping-address-form.tsx (Client Component)
└── useActionState(addAddress / updateAddress / deleteAddress, initialState)
    └── _actions/add-address.ts 等 ("use server")
        ├── zod バリデーション
        ├── API POST /customers/{id}/addresses 等
        └── revalidateTag("customer-{id}")
```

---

## 型定義

```typescript
// types/customer.ts
export type MemberRank = "BRONZE" | "SILVER" | "GOLD";

export type Address = {
  postalCode: string;
  prefecture: string;
  city: string;
  street: string;
};

export type ShippingAddress = {
  id: string;
  address: Address;
  isDefault: boolean;
};

export type Customer = {
  id: string;
  name: string;
  email: string;
  memberRank: MemberRank;
  shippingAddresses: ShippingAddress[];
};
```

```typescript
// types/order.ts
export type OrderStatus =
  | "CONFIRMED" | "PAID" | "PREPARING" | "SHIPPED" | "DELIVERED" | "CANCELLED";

export type OrderItem = {
  id: string;
  productName: string;
  quantity: number;
  unitPrice: number;
};

export type Order = {
  id: string;
  status: OrderStatus;
  totalAmount: number;
  createdAt: string;
  items: OrderItem[];
};
```

---

## 採用ライブラリ

| カテゴリ | パッケージ | 理由 |
|---|---|---|
| フレームワーク | `next@15`, `react@19`, `react-dom@19` | App Router v15 |
| 言語 | `typescript` | 型安全 |
| スタイリング | `tailwindcss` | ユーティリティCSS |
| UIコンポーネント | `shadcn/ui`（CLI） | Tailwind ベース、RSC 対応 |
| クラス結合 | `clsx`, `tailwind-merge` | `cn()` ヘルパー用 |
| バリアント | `class-variance-authority` | shadcn/ui が依存 |
| アイコン | `lucide-react` | shadcn/ui と統一感 |
| バリデーション | `zod` | スキーマ定義 |
| フォーム | `@conform-to/react`, `@conform-to/zod` | Server Actions + useActionState との統合 |
| サーバー保護 | `server-only` | フェッチ層の Client Bundle 混入防止 |

> SWR / React Query / tRPC は **不採用**。Server Components + Server Actions で完結させる。

---

## 技術的な判断・トレードオフ

### conform を選んだ理由
- `useActionState` との統合が自然（`form.id` を Server Actions に渡す設計）
- バリデーションエラーを `throw` せず戻り値で扱える（`nextjs-coding` スキルの方針と一致）
- React Hook Form は Client Components 前提のため App Router との相性が悪い

### 注文履歴を Suspense で遅延する理由
- 顧客プロフィール・住所は即時表示が必要
- 注文履歴は件数が多く API 応答が遅い可能性がある
- Suspense により TTFB を改善しつつ CLS を抑えるためスケルトンと高さを揃える

### `React.cache()` でメモ化する理由
- `getCustomer()` が ProfileContainer と AddressListContainer の両方から呼ばれる
- `fetch()` の Request Memoization はバックエンド API 呼び出しには有効だが、明示的にキャッシュキーを揃える必要がある
- `React.cache()` で関数レベルでメモ化することで確実に重複排除する

---

## 影響範囲
- 新規ディレクトリ（`frontend/`）の新設のため、既存コードへの影響なし
- バックエンド API の変更は不要（既存エンドポイントを利用）
