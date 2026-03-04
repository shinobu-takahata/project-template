---
name: nextjs-review
description: "Next.js App Router のコードをレビューするときに使うスキル。データフェッチ・コンポーネント設計・キャッシュ・レンダリング・認証・エラーハンドリングの観点で問題を指摘する。ユーザーが Next.js のコードレビューを依頼したとき・PR レビュー・コードの問題点を確認したいときは必ずこのスキルを使う。"
---

# Next.js App Router コードレビューガイド

参考書籍: 「Next.jsの考え方」(akfm_sato著、v15対応)

レビュー時は以下のチェック項目を順番に確認し、問題があれば **問題点・理由・修正例** の3点セットで指摘する。

---

## チェックリスト

### 🔴 データフェッチ（重大度: 高）

**[ ] データフェッチが Client Components で行われていないか**
- `"use client"` 内で SWR / React Query / fetch を使ってデータ取得していたら指摘
- 理由: サーバー間通信を活かせない、バンドルサイズ増加、セキュリティリスク
- 修正: Server Components に移動して async/await で直接フェッチ

**[ ] `"use server"` を Server Components に付けていないか**
- `export async function Page()` などに `"use server"` がついていたら指摘
- 理由: `"use server"` は Server Functions（Actions）のためのもの。Server Components には不要
- 修正: `"use server"` を削除する

**[ ] Props Drilling（バケツリレー）が発生していないか**
- ページで全データ取得 → 子・孫コンポーネントへ props で渡し続けるパターン
- 理由: コンポーネントの独立性が失われ、変更コストが増加
- 修正: 各コンポーネントで自分が必要なデータを直接フェッチ（Request Memoization が重複排除）

**[ ] データフェッチ関数に `server-only` が付いているか**
- `import "server-only"` がないフェッチ関数が Client Bundle に混入するリスク
- 修正: フェッチ関数ファイルの先頭に `import "server-only"` を追加

**[ ] 独立したデータフェッチが直列になっていないか**
- 同一コンポーネント内で `await fetchA(); await fetchB();` のように直列に並んでいたら指摘
- 修正: `Promise.all([fetchA(), fetchB()])` またはコンポーネント分割

**[ ] N+1 データフェッチが発生していないか**
- ループ内・リスト系コンポーネントで1件ずつフェッチしているパターン
- 修正: DataLoader でバッチ処理（バックエンドにバッチ API が必要）

---

### 🔴 コンポーネント設計（重大度: 高）

**[ ] Client Components の範囲が必要以上に広くないか**
- Server Components の親・中間層に `"use client"` が付いていたら指摘
- 理由: 配下のすべてのモジュールが Client Bundle に入る（バンドルサイズ肥大化）
- 修正: `"use client"` はコンポーネントツリーの末端（葉）に限定

**[ ] Client Components が Server Components を直接 import していないか**
- `"use client"` のコンポーネント内で Server Components をインポートすることはできない
- 修正: Composition パターンで `children` props として渡す

**[ ] 再利用可能な Presentational Components がテスト可能か**
- データフェッチと表示が1つのコンポーネントに混在していないか
- 推奨: Container（データフェッチ、Server Components）/ Presentational（表示のみ、Shared Components）に分離

---

### 🟡 キャッシュ（重大度: 中）

**[ ] Static Rendering で十分なページが Dynamic Rendering になっていないか**
- `cookies()` / `headers()` / `{ cache: "no-store" }` を不必要に使っていたら指摘
- 理由: Dynamic Rendering はリクエストごとにレンダリングするためパフォーマンスに影響

**[ ] `cache: "no-store"` の意味を理解しているか**
- `no-store` は Data Cache の無効化だけでなく Dynamic Rendering への切り替えも発生させる
- 認証不要の公開データに `no-store` を使っていたら指摘

**[ ] Data Cache のタグが Server Actions の revalidate と対応しているか**
- `fetch(..., { next: { tags: ["products"] } })` に対して `revalidateTag("products")` が呼ばれているか

**[ ] DB アクセスに React.cache() が使われているか**
- `fetch()` の Request Memoization は DB には効かない
- 修正: `import { cache } from "react"` でデータフェッチ関数をラップ

**[ ] `revalidatePath()` / `revalidateTag()` を多用していないか**
- 不必要な広範囲 revalidate は Router Cache の全破棄につながりパフォーマンス劣化
- 修正: タグを細かく設定して影響範囲を限定

---

### 🟡 レンダリング（重大度: 中）

**[ ] Server Components から cookies().set() を呼んでいないか**
- Server Components は純粋関数であるべきで副作用はNG
- 修正: Server Actions（`"use server"` 関数）内で行う

**[ ] 重い処理に Suspense が使われているか**
- 1秒以上かかるデータフェッチを含むコンポーネントが Suspense でラップされていないとページ全体がブロックされる
- 修正: `<Suspense fallback={<Skeleton />}>` でラップ

**[ ] ネストした非同期コンポーネントが直列になっていないか**
- 親コンポーネントが await してから子コンポーネントが await → ウォーターフォール
- 修正: preload パターンまたはコンポーネント分割で並行化

---

### 🟡 認証・認可（重大度: 高 — セキュリティリスク）

**[ ] layout だけで認可チェックしていないか（重大）**
- `layout.tsx` でのみ `verifySession()` を呼んでいたら必ず指摘
- 理由: layout とページは並行レンダリングされるため、layout の認可が先に実行される保証がない → 情報漏洩リスク
- 修正: 各ページで個別に認可チェックを行う

**[ ] 認可チェックがデータアクセス層にもあるか**
- ページで認可チェックしても、フェッチ関数が直接呼ばれると認可をバイパスできる
- 修正: データフェッチ関数内でも `getSession()` → `unauthorized()` の認可を入れる

---

### 🟡 エラーハンドリング（重大度: 中）

**[ ] error.tsx が Client Components になっているか**
- `"use client"` がない `error.tsx` は動作しない
- 修正: ファイル先頭に `"use client"` を追加

**[ ] Server Actions で予測可能なエラーを throw していないか**
- バリデーションエラーなど想定内のエラーを `throw new Error(...)` していたら指摘
- 理由: throw すると `error.tsx` が表示されフォーム入力が失われる
- 修正: `return { error: "..." }` のように戻り値でエラーを表現

**[ ] notFound() / unauthorized() が適切に使われているか**
- 404 → `notFound()`（not-found.tsx が表示される）
- 401/403 → `unauthorized()` または `redirect("/login")`

---

### 🟢 パフォーマンス・コード品質（重大度: 低）

**[ ] layout.tsx の Route Segment Config が下層ページに意図せず影響していないか**
- `layout.tsx` に `export const dynamic = "force-dynamic"` があると配下の全ページが Dynamic Rendering になる

**[ ] v14 と v15 の fetch デフォルト動作の違いを把握しているか**
- v14: `fetch()` のデフォルトは `cache: "force-cache"`
- v15: `fetch()` のデフォルトはキャッシュ無効（ただし Rendering は Static のまま）

**[ ] `staleTimes` の設定がアプリ特性に合っているか**
- v15 デフォルト: `dynamic: 0秒`（データが変わりやすいアプリでは適切、SNS 等では変更を検討）

---

## レビューコメントの書き方

問題を指摘するときは必ずこの3点を含める:

1. **何が問題か** — 具体的なコード箇所を指摘
2. **なぜ問題か** — パフォーマンス/セキュリティ/保守性のどれに影響するか
3. **どう直すか** — 修正後のコードスニペット（短くてよい）

例:
> **[データフェッチ]** `ProductList` が `"use client"` 内で `useSWR` を使ってデータ取得しています。
>
> App Router では Server Components で直接 `fetch` するほうが高速で安全です（サーバー間通信、バンドルサイズ削減）。
>
> ```tsx
> // Before (Client)
> "use client";
> const { data } = useSWR("/api/products", fetcher);
>
> // After (Server)
> export async function ProductList() {
>   const products = await getProducts(); // server-only な fetcher
>   return <ul>{products.map(p => <li key={p.id}>{p.name}</li>)}</ul>;
> }
> ```
