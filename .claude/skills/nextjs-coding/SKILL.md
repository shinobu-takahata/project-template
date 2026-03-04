---
name: nextjs-coding
description: "Next.js App Router でコーディングするときに使うスキル。データフェッチ・コンポーネント設計・キャッシュ・レンダリング・認証・エラーハンドリングのベストプラクティスをガイドする。ユーザーが Next.js のコードを書く・実装する・新しいページ/コンポーネントを作るときは必ずこのスキルを参照する。"
---

# Next.js App Router コーディングガイド

参考書籍: 「Next.jsの考え方」(akfm_sato著、v15対応)

---

## 基本原則

- **Server Components がデフォルト** — `"use client"` がなければすべてサーバーで動く
- **`"use server"` は Server Components に書かない** — これは Server Functions（Server Actions）のためのもの
- **データフェッチはサーバー側で** — Client Components での SWR/React Query は避ける

---

## 第1部: データフェッチ

### Server Components でデータフェッチする

```tsx
// ✅ Good: Server Components で直接 async/await
export async function ProductTitle({ id }: { id: string }) {
  const res = await fetch(`https://api.example.com/products/${id}`);
  const product = await res.json();
  return <div>{product.title}</div>;
}

// ❌ Bad: Client Components でデータフェッチ
"use client";
export function ProductTitle({ id }: { id: string }) {
  const { data } = useSWR(`/api/products/${id}`, fetcher); // 避ける
  return <div>{data?.title}</div>;
}
```

### データフェッチのコロケーション（Props Drilling 廃止）

```tsx
// ✅ Good: 各コンポーネントが自分で必要なデータをフェッチ
// Request Memoization により実際の HTTP リクエストは1回のみ
export default function ProductPage({ id }: { id: string }) {
  return (
    <>
      <ProductHeader id={id} />  {/* 内部で fetchProduct(id) */}
      <ProductDetail id={id} />  {/* 内部で fetchProduct(id) — 重複しない */}
    </>
  );
}

// ❌ Bad: ページで全データ取得して props で渡す（バケツリレー）
export default async function ProductPage({ id }: { id: string }) {
  const product = await fetchProduct(id);
  return <ProductContents product={product} />; // Props Drilling
}
```

### データフェッチ層を分離して `server-only` で保護

```ts
// app/products/_lib/fetcher.ts
import "server-only"; // Client Bundle に誤混入したらビルドエラーになる

export async function getProduct(id: string) {
  const res = await fetch(`https://api.example.com/products/${id}`);
  return res.json();
}
```

### 並行データフェッチ（パフォーマンス最優先）

```tsx
// パターン1: コンポーネント分割（兄弟は自動的に並行レンダリング）
export default function Page({ id }: { id: string }) {
  return (
    <>
      <PostBody postId={id} />    {/* 並行 */}
      <Comments postId={id} />   {/* 並行 */}
    </>
  );
}

// パターン2: Promise.all（同コンポーネント内で複数フェッチ）
const [user, posts] = await Promise.all([
  getUser(id),
  getPosts(id),
]);

// パターン3: preload パターン（ウォーターフォール回避）
export default function Page({ id }: { id: string }) {
  preloadCurrentUser(); // await しない — 子孫での利用に先行してフェッチ開始
  return <Product productId={id} />;
}
```

### N+1 問題は DataLoader で解消

```ts
import DataLoader from "dataloader";
import { cache } from "react";

// React.cache() でリクエストスコープのシングルトン
const getUserLoader = cache(() =>
  new DataLoader(async (ids: readonly string[]) => {
    const users = await batchGetUsers(ids);
    return ids.map(id => users.find(u => u.id === id));
  })
);

export async function getUser(id: string) {
  return getUserLoader().load(id);
}
```

### ユーザー操作のデータフェッチは Server Functions + useActionState

```ts
// app/actions.ts
"use server";
export async function searchProducts(_prev: Product[], formData: FormData) {
  const query = formData.get("query") as string;
  const res = await fetch(`https://api.example.com/products/search?q=${query}`);
  return res.json();
}
```

```tsx
// app/form.tsx
"use client";
import { useActionState } from "react-dom";
import { searchProducts } from "./actions";

export default function Form() {
  const [products, action] = useActionState(searchProducts, []);
  return (
    <form action={action}>
      <input name="query" />
      <button>Search</button>
    </form>
  );
}
```

---

## 第2部: コンポーネント設計

### `"use client"` と `"use server"` はバンドル境界の宣言

| ディレクティブ | 意味 |
|---|---|
| なし | Server Components（デフォルト） |
| `"use client"` | サーバー→クライアントのバンドル境界 |
| `"use server"` | Server Functions の宣言（Server Components には不要！） |

重要: `"use client"` から import されたモジュールは**すべて** Client Bundle に入る。

### Client Components を使う3つのケース

1. **ブラウザ API・イベントハンドラ・Hooks を使う**（onClick, useState, useEffect など）
2. **RSC 未対応のサードパーティライブラリを使う**（ラッパーを作って Client Boundary を明示）
3. **RSC Payload 転送量を削減したい**（大量の Tailwind クラスなど）

### Composition パターン（Client Components の中に Server Components を入れる）

```tsx
// ✅ Good: children で Server Components を受け取る
// side-menu.tsx（Client Components）
"use client";
export function SideMenu({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      {children}  {/* Server Components を渡せる */}
      <button onClick={() => setOpen(p => !p)}>toggle</button>
    </>
  );
}

// page.tsx（Server Components）
export default function Page() {
  return (
    <SideMenu>
      <UserInfo />  {/* Server Components — OK! */}
    </SideMenu>
  );
}
```

### Container/Presentational パターン（テスト容易性向上）

```tsx
// Container（Server Components）— データフェッチ担当
export async function ArticleContainer({ id }: { id: string }) {
  const article = await getArticle(id);
  return <ArticlePresenter article={article} />;
}

// Presentational（Shared Components）— テスト可能
export function ArticlePresenter({ article }: { article: Article }) {
  return <article>{article.content}</article>;
}
```

---

## 第3部: キャッシュ

### Static / Dynamic Rendering を意識する

| レンダリング | タイミング | 使いどき |
|---|---|---|
| Static Rendering | ビルド時 | ユーザー固有情報なし |
| Dynamic Rendering | リクエスト時 | 認証・個別データあり |

Dynamic Rendering へのオプトイン方法:
```tsx
// cookies/headers を使う（自動的に Dynamic になる）
const cookieStore = await cookies();

// fetch に no-store を指定（v15: デフォルトはキャッシュ無効だが Rendering は Static）
await fetch("https://...", { cache: "no-store" });

// Route Segment Config
export const dynamic = "force-dynamic";
```

### Data Cache の活用（Dynamic Rendering のパフォーマンス改善）

```ts
// タグ付きキャッシュ（Server Actions で revalidate 可能）
await fetch("https://...", { next: { tags: ["products"], revalidate: 3600 } });

// DB アクセス等は unstable_cache を使う
const getCachedUser = unstable_cache(getUser, ["user"], { tags: ["users"], revalidate: 60 });
```

### DB アクセスは React.cache() でメモ化

```ts
import { cache } from "react";

// fetch() の Request Memoization は DB には効かないので手動でメモ化
export const getPost = cache(async (id: number) => {
  return db.query.posts.findFirst({ where: eq(posts.id, id) });
});
```

### Server Actions でのデータ操作

```ts
// app/actions.ts
"use server";
import { revalidateTag } from "next/cache";
import { redirect } from "next/navigation";

export async function createTodo(formData: FormData) {
  await db.insert(todos).values({ text: formData.get("text") });
  revalidateTag("todos");    // キャッシュ更新
  redirect("/todos");         // リダイレクト（1往復で完結）
}
```

---

## 第4部: レンダリング

### Server Components の純粋性を保つ

- Server Components から `cookies().set()` / `cookies().delete()` は**呼べない**（副作用禁止）
- データ変更は必ず Server Actions（`"use server"`の関数）で行う
- 同じ入力 → 同じ出力になるよう設計する

### Suspense + Streaming で重い処理を遅延

```tsx
import { Suspense } from "react";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <div>
      <h1>タイトル（即座に表示）</h1>
      <Suspense fallback={<Skeleton />}>
        <HeavyDataComponent />  {/* 1秒以上かかるなら Suspense で遅延 */}
      </Suspense>
    </div>
  );
}
```

---

## 第5部: その他

### URL パラメータの参照

```tsx
// Server Components — params/searchParams は Promise（v15）
export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ sort?: string }>;
}) {
  const { id } = await params;
  const { sort } = await searchParams;
}

// Client Components
"use client";
const params = useParams<{ id: string }>();
const searchParams = useSearchParams();
```

### 認証・認可

```tsx
// ❌ Bad: layout だけで認可チェック（ページと並行レンダリングされるため不十分）
export default async function DashboardLayout({ children }) {
  await verifySession(); // これだけでは情報漏洩リスクあり
}

// ✅ Good: 各ページで必ず認可チェック
export default async function Page() {
  await verifySession(); // ページ個別にチェック
}

// ✅ Good: データアクセス層でも認可チェック
export async function getPremiumContent(id: string) {
  const session = await getSession();
  if (!session?.isPremiumUser) unauthorized();
  return fetchContent(id);
}
```

### エラーハンドリング

```tsx
// error.tsx は必ず Client Components にする
"use client";
export default function ErrorPage({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div>
      <h2>エラーが発生しました</h2>
      <button onClick={reset}>再試行</button>
    </div>
  );
}
```

```ts
// ❌ Bad: Server Actions で throw するとフォーム入力が消える
"use server";
export async function submit(formData: FormData) {
  if (!valid) throw new Error("バリデーションエラー"); // フォームが消える！
}

// ✅ Good: 予測可能なエラーは戻り値で表現する
"use server";
export async function submit(prevState: unknown, formData: FormData) {
  const result = parseWithZod(formData, { schema });
  if (result.status !== "success") return result.reply(); // throw しない
}
```
