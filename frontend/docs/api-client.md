# api-client.ts

## 概要

`lib/api-client.ts` はバックエンド API との HTTP 通信を担うクライアントユーティリティ。全機能で共有する薄いラッパーで、`fetch` を内部で使用する。レスポンスの型指定・エラーハンドリング・ベース URL 設定を一元管理する。

## 基本的な使い方

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

## 環境変数

ベース URL は環境変数 `NEXT_PUBLIC_API_URL` で制御する。

| 環境変数 | デフォルト値 | 説明 |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | バックエンド API のベース URL |

## server-only との組み合わせ

`fetcher.ts` など、サーバーサイドのみで使う関数は `import "server-only"` を先頭に記述することで、Client Component からの誤った import をビルド時にエラーにする。

```typescript
// _lib/fetcher.ts
import "server-only";

export const getCustomer = cache(async (id: string): Promise<Customer> => {
  return apiClient.get<Customer>(`/customers/${id}`, {
    next: { tags: [`customer-${id}`] },
  });
});
```
