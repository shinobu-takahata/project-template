# フロントエンド技術ドキュメント

## 目次

1. [ライブラリ一覧](#1-ライブラリ一覧)
2. [ディレクトリ構造](#2-ディレクトリ構造)
3. [実装方針](#3-実装方針)
4. [ライブラリの使い方](#4-ライブラリの使い方)
5. [テストの方針](#5-テストの方針)
6. [テストの書き方](#6-テストの書き方)

---

## 1. ライブラリ一覧

### フレームワーク・コアライブラリ

| ライブラリ | バージョン | 用途 |
|---|---|---|
| [Next.js](https://nextjs.org/) | 16.x | React フレームワーク。App Router によるファイルベースルーティング、Server Component、Server Action を提供する |
| [React](https://react.dev/) | 19.x | UI コンポーネントライブラリ。`useActionState` など最新の React API を使用する |

### フォーム・バリデーション

| ライブラリ | バージョン | 用途 |
|---|---|---|
| [Zod](https://zod.dev/) | 4.x | スキーマ定義とバリデーション。サーバー・クライアント両側で共有する |
| [@conform-to/react](https://conform.guide/) | 1.x | `useActionState` と連携するフォーム状態管理。フィールドの ID・名前・エラーを管理する |
| [@conform-to/zod](https://conform.guide/api/zod) | 1.x | conform と Zod を連携させるアダプター。`parseWithZod()` でフォームデータをパースする |

### UI・スタイリング

| ライブラリ | バージョン | 用途 |
|---|---|---|
| [Tailwind CSS](https://tailwindcss.com/) | 4.x | ユーティリティファーストの CSS フレームワーク |
| [shadcn/ui](https://ui.shadcn.com/) | 3.x | Tailwind CSS ベースのコンポーネント集。`npx shadcn add` で `components/ui/` に追加し、直接編集してカスタマイズする |
| [Lucide React](https://lucide.dev/) | 0.5x | SVG アイコンライブラリ |

### サーバーサイド

| ライブラリ | バージョン | 用途 |
|---|---|---|
| [server-only](https://www.npmjs.com/package/server-only) | 0.0.1 | `import "server-only"` を記述したファイルを Client Component から import するとビルドエラーにする。`fetcher.ts` などの誤用を防ぐ |

### テスト

| ライブラリ | バージョン | 用途 |
|---|---|---|
| [Jest](https://jestjs.io/) | 29.x | JavaScript テストフレームワーク |
| [@testing-library/react](https://testing-library.com/docs/react-testing-library/intro/) | 16.x | React コンポーネントのレンダリングとクエリを提供するテストユーティリティ |
| [@testing-library/user-event](https://testing-library.com/docs/user-event/intro/) | 14.x | クリック・入力などのユーザー操作をシミュレートするユーティリティ |
| [@testing-library/jest-dom](https://github.com/testing-library/jest-dom) | 6.x | `toBeInTheDocument()` などの DOM 検証用カスタムマッチャーを提供する |

---

## 2. ディレクトリ構造

### 抽象構造（テンプレート）

新しい機能を追加するときに参照するパターン。

```
frontend/
├── app/
│   └── [feature]/                        # 機能名（例: customers, products, orders）
│       ├── layout.tsx                    # 機能共通レイアウト（任意）
│       ├── page.tsx                      # 一覧ページ（Server Component）
│       ├── new/                          # 新規作成ページ
│       │   ├── page.tsx
│       │   ├── _schema.ts                # Zod スキーマ（action と form で共有する場合）
│       │   ├── _actions/
│       │   │   └── create-[entity].ts   # Server Action
│       │   ├── _components/
│       │   │   └── [entity]-new-form.tsx
│       │   └── __tests__/
│       │       ├── schema.test.ts
│       │       └── [entity]-new-form.test.tsx
│       └── [[entityId]]/                 # 詳細・編集ページ
│           ├── page.tsx
│           ├── loading.tsx               # Suspense フォールバック
│           ├── error.tsx                 # エラーバウンダリ（"use client" 必須）
│           ├── not-found.tsx             # 404
│           ├── _lib/
│           │   └── fetcher.ts            # server-only データ取得関数
│           ├── _actions/
│           │   ├── update-[entity].ts
│           │   └── delete-[entity].ts
│           └── _components/
│               └── [section]/            # UI の関心ごとにサブディレクトリを切る
│                   ├── [section]-container.tsx   # Server Component（データ取得）
│                   ├── [section]-list.tsx         # Client Component（表示）
│                   ├── [section]-card.tsx         # Client Component（表示単位）
│                   ├── [section]-form.tsx         # Client Component（入力）
│                   └── __tests__/
│                       └── [section]-card.test.tsx
├── components/
│   └── ui/                       # Shadcn UI（npx shadcn add で追加・直接編集可）
├── lib/
│   ├── api-client.ts             # HTTP クライアント（全機能で共有）
│   └── utils.ts                  # cn() ユーティリティ
├── types/
│   └── [entity].ts               # 型定義（機能ごとにファイルを分ける）
└── __mocks__/
    └── server-only.ts            # Jest 用モック
```

### 実際の構造（customers 機能）

```
frontend/
├── app/                          # Next.js App Router のルート
│   ├── layout.tsx                # Root レイアウト
│   ├── page.tsx                  # Root ページ（/customers へリダイレクト）
│   ├── error.tsx                 # Root エラーバウンダリ
│   ├── globals.css               # グローバルスタイル（Tailwind + Shadcn のトークン定義）
│   └── customers/
│       ├── layout.tsx            # /customers 共通レイアウト
│       ├── page.tsx              # 顧客一覧ページ（Server Component）
│       ├── new/
│       │   ├── page.tsx          # 顧客登録ページ（Server Component）
│       │   ├── _schema.ts        # Zod バリデーションスキーマ
│       │   ├── _actions/
│       │   │   └── create-customer.ts   # Server Action
│       │   ├── _components/
│       │   │   └── customer-new-form.tsx
│       │   └── __tests__/
│       │       ├── schema.test.ts
│       │       └── customer-new-form.test.tsx
│       └── [customerId]/
│           ├── page.tsx          # 顧客詳細ページ（Server Component）
│           ├── loading.tsx       # Suspense フォールバック
│           ├── error.tsx         # エラーバウンダリ
│           ├── not-found.tsx     # 404 ページ
│           ├── _lib/
│           │   └── fetcher.ts    # server-only データ取得関数
│           ├── _actions/
│           │   ├── update-customer.ts
│           │   ├── add-address.ts
│           │   ├── update-address.ts
│           │   └── delete-address.ts
│           └── _components/
│               ├── customer-profile/
│               │   ├── customer-profile-container.tsx  # Server Component（データ取得）
│               │   ├── customer-profile.tsx            # Client Component（表示・編集切替）
│               │   ├── customer-edit-form.tsx          # Client Component（編集フォーム）
│               │   └── __tests__/
│               │       └── customer-edit-form.test.tsx
│               ├── shipping-addresses/
│               │   ├── shipping-address-list-container.tsx  # Server Component
│               │   ├── shipping-address-list.tsx            # Client Component
│               │   ├── shipping-address-card.tsx            # Client Component
│               │   ├── shipping-address-form.tsx            # Client Component
│               │   └── __tests__/
│               │       └── shipping-address-card.test.tsx
│               └── order-history/
│                   ├── order-history-container.tsx  # Server Component（Suspense 境界内）
│                   ├── order-history-list.tsx       # Server Component
│                   ├── order-history-item.tsx       # Server Component
│                   └── order-history-skeleton.tsx   # スケルトン（loading.tsx 用）
├── components/
│   └── ui/                       # Shadcn UI コンポーネント（直接編集しない）
│       ├── badge.tsx
│       ├── button.tsx
│       ├── card.tsx
│       ├── input.tsx
│       ├── label.tsx
│       ├── separator.tsx
│       └── skeleton.tsx
├── lib/
│   ├── api-client.ts             # HTTP クライアント
│   └── utils.ts                  # cn() ユーティリティ
├── types/
│   ├── customer.ts               # Customer, Address, ShippingAddress, MemberRank
│   └── order.ts                  # Order, OrderItem, OrderStatus
├── __mocks__/
│   └── server-only.ts            # Jest 用モック
├── jest.config.js
├── jest.setup.ts
└── next.config.ts
```

### コロケーション規則

Next.js App Router の `_` プレフィックスディレクトリはルーティングから除外される。
同じルートセグメントに関連するコードをまとめる（コロケーション）ことで、削除・変更時の影響範囲を明確にする。

| ディレクトリ | 役割 |
|---|---|
| `_components/` | そのルートセグメント専用の React コンポーネント |
| `_actions/` | そのルートセグメント専用の Server Action |
| `_lib/` | そのルートセグメント専用のユーティリティ（fetcher など） |
| `__tests__/` | テストファイル（対象コンポーネントの隣に配置） |

---

## 3. 実装方針

### Server Component vs Client Component の分離基準

**Server Component にする条件（デフォルト）**
- データベースや API からデータを取得する
- `async/await` を使う
- ユーザーインタラクション・状態管理が不要
- `loading.tsx` / `error.tsx` / `not-found.tsx` は常に Server Component

**Client Component にする条件**
- `useState` / `useReducer` / `useEffect` など React hooks を使う
- ボタンクリック・フォーム入力などのイベントハンドラが必要
- ブラウザ専用 API（`window`, `localStorage`）を使う
- `"use client"` ディレクティブを先頭に記述する

### Container / Presentational パターン

データ取得と表示を分離することで、Client Component のテストを容易にする。

```
*-container.tsx（Server Component）
  └─ データ取得（fetcher.ts 経由）
      └─ *-list.tsx / *-profile.tsx（Client Component）
          └─ *-card.tsx / *-form.tsx（Client Component）
```

**例: 顧客プロフィールセクション**

```
CustomerProfileContainer（Server）
  getCustomer(id) → Customer データ取得
    └─ CustomerProfile（Client）
        ├─ 表示モード: 顧客情報を表示
        └─ 編集モード: CustomerEditForm を表示
            └─ updateCustomer（Server Action）
```

### Server Action によるデータ変更

Server Action は `"use server"` ファイルに定義し、**async function のみ export** する。
Zod スキーマを同じファイルに書く場合、Server Action と同じファイルに定義できる。
ただし、フォームコンポーネントとスキーマを共有する場合は `_schema.ts` に切り出す。

```typescript
// _actions/update-customer.ts
"use server";

export async function updateCustomer(
  customerId: string,
  _prevState: unknown,
  formData: FormData,
) {
  const submission = parseWithZod(formData, { schema });
  if (submission.status !== "success") {
    return submission.reply(); // エラーをクライアントに返す
  }
  await apiClient.put(`/customers/${customerId}`, submission.value);
  revalidateTag(`customer-${customerId}`, { expire: 0 }); // キャッシュ無効化
  return submission.reply();
}
```

**`"use server"` ファイルでのスキーマ共有問題**

`"use server"` ファイルは async function 以外を export できないため、
フォームコンポーネントとスキーマを共有する場合は別ファイルに切り出す。

```
new/
├── _schema.ts              ← Zod スキーマを定義（"use server" なし）
├── _actions/
│   └── create-customer.ts  ← _schema.ts から import
└── _components/
    └── customer-new-form.tsx ← _schema.ts から import
```

### キャッシング戦略

```typescript
// _lib/fetcher.ts
import "server-only";
import { cache } from "react";

export const getCustomer = cache(async (id: string): Promise<Customer> => {
  return apiClient.get<Customer>(`/customers/${id}`, {
    next: { tags: [`customer-${id}`] }, // キャッシュタグ設定
  });
});
```

| 機能 | 役割 |
|---|---|
| `React.cache()` | 同一リクエスト内の重複 fetch を排除（メモ化） |
| `next: { tags: [...] }` | タグベースのキャッシュ。Server Action 後に `revalidateTag()` で無効化 |
| `{ expire: 0 }` | `revalidateTag()` に渡すと即座にキャッシュを破棄する |

### `server-only` の使用

`fetcher.ts` の先頭に `import "server-only"` を記述することで、
Client Component からの誤った import をビルド時にエラーにする。

---

## 4. ライブラリの使い方

### Next.js App Router

特殊なファイル名で機能が決まる。

| ファイル | 役割 |
|---|---|
| `page.tsx` | ルートのメインコンテンツ |
| `layout.tsx` | 複数ページで共有するラッパー |
| `loading.tsx` | Suspense のフォールバック UI |
| `error.tsx` | エラーバウンダリ（`"use client"` 必須） |
| `not-found.tsx` | 404 UI（`notFound()` 関数で表示） |

```tsx
// page.tsx での params 受け取り例
// Next.js 15 以降、動的ルート（app/posts/[id]/page.tsxみたいなやつ）の params は Promise 型になった。必ず await する。
export default async function CustomerDetailPage({
  params,
}: {
  params: Promise<{ customerId: string }>;
}) {
  const { customerId } = await params;

  return (
    <div>
      <CustomerProfileContainer customerId={customerId} />
      <Suspense fallback={<OrderHistorySkeleton />}>
        <OrderHistoryContainer customerId={customerId} />
      </Suspense>
    </div>
  );
}
```

### @conform-to/react + Zod v4

フォーム状態管理は `useActionState` + `useForm` の組み合わせで行う。
useActionStateは、フォームアクションの結果に基づいてステートを更新するためのフックである。

```tsx
"use client";

import { useActionState } from "react";
import { useForm } from "@conform-to/react";
import { parseWithZod } from "@conform-to/zod/v4";

export function SomeForm() {
  // useActionState: Server Action の実行状態を管理
  const [lastResult, action] = useActionState(serverAction, null);

  // useForm: フォーム状態とエラーを管理
  const [form, fields] = useForm({
    lastResult,
    onValidate({ formData }) {
      return parseWithZod(formData, { schema }); // クライアント側バリデーション
    },
    shouldValidate: "onBlur",      // フォーカスアウト時にバリデーション
    shouldRevalidate: "onInput",   // 入力中にリバリデーション
  });

  return (
    <form id={form.id} onSubmit={form.onSubmit} action={action} noValidate>
      <input
        id={fields.name.id}
        name={fields.name.name}
        aria-invalid={!!fields.name.errors} // エラー時に aria-invalid="true"
      />
      {fields.name.errors && (
        <p>{fields.name.errors[0]}</p>
      )}
    </form>
  );
}
```

**重要な注意事項**

`@conform-to/zod/v4` は空のフォームフィールドを `""` ではなく `undefined` に変換する。
そのため `z.string().min(1, "メッセージ")` のカスタムメッセージは空値には適用されない。

| 値 | Zod の挙動 |
|---|---|
| `"invalid@"` | `z.string().email(...)` → カスタムメッセージが表示される |
| `""` (空入力) | conform が `undefined` に変換 → 型エラーメッセージが表示される |

**ネストされたオブジェクト（住所フォームなど）**

```tsx
const shippingAddress = fields.shipping_address.getFieldset();

<input name={shippingAddress.postal_code.name} /> // "shipping_address.postal_code"
```

### api-client.ts

```typescript
import { apiClient } from "@/lib/api-client";

// GET: レスポンスの型を指定する
const customer = await apiClient.get<Customer>(`/customers/${id}`);

// GET: キャッシュタグを設定する（Server Component 内）
const customer = await apiClient.get<Customer>(`/customers/${id}`, {
  next: { tags: [`customer-${id}`] },
});

// POST: リクエストボディを渡す
const result = await apiClient.post<{ id: string }>("/customers", { name, email });

// PUT: 更新
await apiClient.put(`/customers/${id}`, { name, email });

// DELETE: 204 は undefined を返す
await apiClient.delete(`/customers/${id}/addresses/${addressId}`);
```

ベース URL は環境変数 `NEXT_PUBLIC_API_URL` で制御する（デフォルト: `http://localhost:8000/api/v1`）。

### Shadcn UI + Tailwind CSS

**コンポーネントの追加**

```bash
npx shadcn add <component-name>
# 例: npx shadcn add dialog
```

追加されたコンポーネントは `components/ui/` に配置される。直接編集してカスタマイズしてよい。

**クラスの合成**

```typescript
import { cn } from "@/lib/utils";

// clsx + tailwind-merge を組み合わせた cn() を使う
<div className={cn("base-class", isActive && "active-class", className)} />
```

**Shadcn コンポーネントの使い方**

```tsx
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

<Button variant="outline" size="sm">キャンセル</Button>
<Badge variant="destructive">キャンセル済</Badge>
```


## 5. テストの方針

### テストフェーズと対象

| フェーズ | 対象 | ツール | 状態 |
|---|---|---|---|
| 単体テスト | Client Component の操作 / Zod スキーマ検証 | Jest + React Testing Library | 実装済 |
| 結合テスト | Server Action〜API連携 / エラーレスポンスの表示 | Jest + MSW | 未実装 |
| システムテスト | ユーザーシナリオ全体 | Playwright | 未実装 |

### 単体テストの対象

**対象にする**
- `_schema.ts`（Zod スキーマ）: バリデーションルールの正確性を確認
- Client Component:
  - フォームのバリデーション表示（`aria-invalid` 属性、エラーメッセージ）
  - UI 状態の切り替え（編集モード / 表示モードの切替など）
  - ボタンクリックによるコールバック呼び出し（`onCancel` など）
  - 初期値の表示

**対象にしない（理由）**
| 対象外 | 理由 | 代替 |
|---|---|---|
| async Server Component（`page.tsx`, `*-container.tsx`） | Jest は async サーバーコンポーネントに非対応 | Playwright |
| Server Action（`_actions/*.ts`） | API 連携含む結合テストが適切 | Jest + MSW（結合テスト） |
| `fetcher.ts` | `server-only` + `React.cache` のモックが複雑 | Playwright |

### 既知の注意事項

**1. conform + Zod v4 の空フィールドの挙動**

空フィールドは `undefined` に変換されるため、空値バリデーションは `aria-invalid` 属性で確認する。

```tsx
// NG: 空値に対しカスタムメッセージは表示されない
expect(screen.getByText("名前を入力してください")).toBeInTheDocument();

// OK: aria-invalid でバリデーション失敗を確認する
expect(screen.getByLabelText("名前")).toHaveAttribute("aria-invalid", "true");
```

**2. Server Action のモック**

`"use server"` ファイルは `jest.mock()` でモックする。`next/cache` などの依存も自動的にモックされる。

---

## 6. テストの書き方

### セットアップ

```
jest.config.js         ← ts-jest + jsdom + @/ パスエイリアス + server-only モック
jest.setup.ts          ← @testing-library/jest-dom のグローバル設定
__mocks__/
  server-only.ts       ← import "server-only" を無効化するモック
```

```bash
# テストの実行
npm test

# ウォッチモード（開発時）
npm run test:watch
```

### テストファイルの配置

対象コンポーネントと同じディレクトリに `__tests__/` を作成し、その中に配置する。

```
_components/
  customer-profile/
    customer-edit-form.tsx
    __tests__/
      customer-edit-form.test.tsx   ← ここに配置
```

### モックパターン

**Server Action のモック**

```tsx
// テストファイルの先頭（import の前）
jest.mock("../../../_actions/update-customer", () => ({
  updateCustomer: jest.fn(),
}));
```

パスは**テストファイルから見た相対パス**で指定する。

**子コンポーネントのモック**

内部で `useActionState` などを使う複雑な子コンポーネントはモックして単純化する。

```tsx
jest.mock("../shipping-address-form", () => ({
  ShippingAddressForm: ({ onCancel }: { onCancel: () => void }) => (
    <div data-testid="shipping-address-form">
      <button onClick={onCancel}>キャンセル</button>
    </div>
  ),
}));
```

### クエリの選び方（優先順）

| 優先度 | クエリ | 使うとき |
|---|---|---|
| 1 | `getByRole` | ボタン、テキストボックス、チェックボックスなど |
| 2 | `getByLabelText` | `<label>` と紐づいた入力要素 |
| 3 | `getByText` | 表示テキストで探す |
| 4 | `getByTestId` | モックコンポーネント内など（最終手段） |

### コード例

#### パターン1: Zod スキーマのテスト

```typescript
import { createCustomerSchema } from "../_schema";

describe("createCustomerSchema", () => {
  it("全フィールド有効値でバリデーション成功", () => {
    const result = createCustomerSchema.safeParse({
      name: "山田太郎",
      email: "taro@example.com",
      shipping_address: {
        label: "自宅",
        postal_code: "100-0001",
        prefecture: "東京都",
        city: "千代田区",
        street: "千代田1-1-1",
      },
    });
    expect(result.success).toBe(true);
  });

  it("name が空文字のとき失敗し、カスタムメッセージが返る", () => {
    const result = createCustomerSchema.safeParse({ name: "", email: "a@b.com", ... });
    expect(result.success).toBe(false);
    if (!result.success) {
      const errors = result.error.issues.filter((i) => i.path.includes("name"));
      expect(errors[0].message).toBe("名前を入力してください");
    }
  });
});
```

#### パターン2: 表示テスト（静的）

```tsx
import { render, screen } from "@testing-library/react";
import { ShippingAddressCard } from "../shipping-address-card";

// Server Action などの依存をモック
jest.mock("../../../_actions/delete-address", () => ({
  deleteAddress: jest.fn(),
}));
jest.mock("../shipping-address-form", () => ({
  ShippingAddressForm: () => <div />,
}));

it("isDefault が true のとき「デフォルト住所」バッジが表示される", () => {
  render(
    <ShippingAddressCard
      customerId="cust-1"
      address={{ id: "addr-1", address: { ... }, isDefault: true }}
    />
  );
  expect(screen.getByText("デフォルト住所")).toBeInTheDocument();
});
```

#### パターン3: インタラクションテスト（userEvent）

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

it("編集ボタンをクリックすると ShippingAddressForm が表示される", async () => {
  const user = userEvent.setup(); // 必ず setup() を使う
  render(<ShippingAddressCard customerId="cust-1" address={baseAddress} />);

  await user.click(screen.getByRole("button", { name: "編集" }));

  expect(screen.getByTestId("shipping-address-form")).toBeInTheDocument();
});

it("フォームでキャンセルすると元の表示に戻る", async () => {
  const user = userEvent.setup();
  render(<ShippingAddressCard customerId="cust-1" address={baseAddress} />);

  await user.click(screen.getByRole("button", { name: "編集" }));
  await user.click(screen.getByRole("button", { name: "キャンセル" }));

  expect(screen.queryByTestId("shipping-address-form")).not.toBeInTheDocument();
});
```

#### パターン4: フォームバリデーションテスト

```tsx
// 空フィールドのバリデーション → aria-invalid で確認
it("name を空にしてフォーカスアウトすると invalid になる", async () => {
  const user = userEvent.setup();
  render(<CustomerEditForm customer={baseCustomer} onCancel={jest.fn()} />);

  await user.clear(screen.getByLabelText("名前"));
  await user.tab(); // フォーカスアウト

  expect(screen.getByLabelText("名前")).toHaveAttribute("aria-invalid", "true");
});

// フォーマットエラー → エラーメッセージで確認
it("email に不正なフォーマットを入力するとエラーメッセージが表示される", async () => {
  const user = userEvent.setup();
  render(<CustomerEditForm customer={baseCustomer} onCancel={jest.fn()} />);

  await user.type(screen.getByLabelText("メール"), "not-an-email");
  await user.tab();

  expect(
    screen.getByText("有効なメールアドレスを入力してください")
  ).toBeInTheDocument();
});
```

#### パターン5: コールバック呼び出しテスト

```tsx
it("キャンセルボタンをクリックすると onCancel が呼ばれる", async () => {
  const user = userEvent.setup();
  const onCancel = jest.fn();
  render(<CustomerEditForm customer={baseCustomer} onCancel={onCancel} />);

  await user.click(screen.getByRole("button", { name: "キャンセル" }));

  expect(onCancel).toHaveBeenCalledTimes(1);
});
```
