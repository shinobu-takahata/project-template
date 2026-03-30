# フロントエンド技術ドキュメント

## 目次

1. [ライブラリ一覧](#1-ライブラリ一覧)
2. [ディレクトリ構造](#2-ディレクトリ構造)
3. [実装方針](#3-実装方針)
4. [詳細ドキュメント](#4-詳細ドキュメント)

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

---

## 4. 詳細ドキュメント

各ライブラリの詳細な使い方・テストの書き方は個別ドキュメントを参照。

| ドキュメント | 内容 |
|---|---|
| [docs/nextjs.md](docs/nextjs.md) | Next.js App Router の特殊ファイル・動的ルート・Server Action・キャッシング |
| [docs/conform-zod.md](docs/conform-zod.md) | @conform-to/react + Zod v4 によるフォーム状態管理とバリデーション |
| [docs/api-client.md](docs/api-client.md) | api-client.ts による HTTP 通信・環境変数設定 |
| [docs/shadcn-tailwind.md](docs/shadcn-tailwind.md) | Shadcn UI + Tailwind CSS によるコンポーネントとスタイリング |
| [docs/testing.md](docs/testing.md) | テスト方針・モックパターン・コード例 |
