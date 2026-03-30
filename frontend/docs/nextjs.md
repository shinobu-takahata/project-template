# Next.js App Router

## 概要

Next.js は React ベースのフルスタックフレームワーク。App Router（`app/` ディレクトリ）を使い、ファイルシステムベースのルーティング・Server Component・Server Action を提供する。バージョン 13 以降の App Router は、従来の Pages Router と異なり、デフォルトでサーバーサイドレンダリングが前提となる設計になっている。

## 特殊ファイル

特殊なファイル名でルーティングの機能が決まる。

| ファイル | 役割 |
|---|---|
| `page.tsx` | ルートのメインコンテンツ |
| `layout.tsx` | 複数ページで共有するラッパー |
| `loading.tsx` | Suspense のフォールバック UI |
| `error.tsx` | エラーバウンダリ（`"use client"` 必須） |
| `not-found.tsx` | 404 UI（`notFound()` 関数で表示） |

## 動的ルートの params

Next.js 15 以降、動的ルート（`app/posts/[id]/page.tsx` など）の `params` は Promise 型になった。必ず `await` する。

```tsx
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

## Server Component vs Client Component

詳細な分離基準は [実装方針](../README.md#3-実装方針) を参照。

**Server Component（デフォルト）**
- API からデータを取得する
- `async/await` を使う
- ユーザーインタラクション・状態管理が不要

**Client Component**
- `useState` / `useEffect` など React hooks を使う
- イベントハンドラが必要
- ブラウザ専用 API を使う
- ファイル先頭に `"use client"` ディレクティブを記述する

## Server Action

`"use server"` ファイルに定義し、**async function のみ export** する。

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
    return submission.reply();
  }
  await apiClient.put(`/customers/${customerId}`, submission.value);
  revalidateTag(`customer-${customerId}`, { expire: 0 });
  return submission.reply();
}
```

`"use server"` ファイルは async function 以外を export できないため、フォームコンポーネントとスキーマを共有する場合は `_schema.ts` に切り出す。

```
new/
├── _schema.ts              ← Zod スキーマを定義（"use server" なし）
├── _actions/
│   └── create-customer.ts  ← _schema.ts から import
└── _components/
    └── customer-new-form.tsx ← _schema.ts から import
```

## キャッシング戦略

```typescript
// _lib/fetcher.ts
import "server-only";
import { cache } from "react";

export const getCustomer = cache(async (id: string): Promise<Customer> => {
  return apiClient.get<Customer>(`/customers/${id}`, {
    next: { tags: [`customer-${id}`] },
  });
});
```

| 機能 | 役割 |
|---|---|
| `React.cache()` | 同一リクエスト内の重複 fetch を排除（メモ化） |
| `next: { tags: [...] }` | タグベースのキャッシュ。Server Action 後に `revalidateTag()` で無効化 |
| `{ expire: 0 }` | `revalidateTag()` に渡すと即座にキャッシュを破棄する |
