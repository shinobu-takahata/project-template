# 要求定義: フロントエンド 顧客管理機能

## 概要
Next.js App Router を用いて、OrderHub の顧客管理ドメインに対応するフロントエンドを構築する。
顧客情報の閲覧・編集、配送先住所の管理、注文履歴の参照を提供するページ群を実装する。

## 背景・目的
- `docs/ddd/product-requirements.md` に定義された顧客管理機能をフロントエンドから操作できるようにする
- Next.js App Router のベストプラクティス（`nextjs-coding` スキル準拠）を実践した実装例として整備する
- DDD の Customer 集約（Customer / ShippingAddress / MemberRank 等）をフロントエンドで適切に扱う

## 受け入れ条件

### 機能
- [ ] 顧客一覧ページ（`/customers`）を表示できる
- [ ] 顧客詳細ページ（`/customers/[customerId]`）で顧客情報・住所・注文履歴を表示できる
- [ ] 顧客情報（名前・メール等）を編集できる
- [ ] 配送先住所を追加・編集・削除できる（最大5件、デフォルト住所1件）
- [ ] 注文履歴一覧を閲覧できる

### 技術
- [ ] データフェッチは Server Components で行う（Client Components での fetch/SWR は使わない）
- [ ] フェッチ関数は `_lib/fetcher.ts` に集約し `server-only` で保護する
- [ ] フォーム操作は Server Actions（`_actions/`）で実装し、バリデーションは戻り値で表現する
- [ ] 注文履歴は `<Suspense>` でストリーミングする
- [ ] `error.tsx` は Client Component にする

## 実装対象

| 対象 | 内容 |
|---|---|
| `frontend/` | Next.js プロジェクト初期セットアップ |
| `app/customers/` | 顧客一覧ページ |
| `app/customers/[customerId]/` | 顧客詳細ページ（プロフィール・住所・注文履歴） |
| `app/customers/new/` | 顧客新規登録ページ |
| `components/ui/` | shadcn/ui コンポーネント |
| `types/` | ドメイン型定義 |
| `lib/` | 共通ユーティリティ |

## 制約事項
- バックエンド API（FastAPI）はすでに実装済みまたはモックで代替する
- 認証・認可は本スコープ外（簡易的なヘッダーのみ）
- Next.js v15 + React 19 を使用する

## スコープ外
- 注文管理・商品管理・在庫管理の画面（別フェーズ）
- 認証フロー（ログイン・ログアウト）
- 管理者向け画面の権限制御
- E2E テスト
