# Shadcn UI + Tailwind CSS

## 概要

### Tailwind CSS

Tailwind CSS はユーティリティファーストの CSS フレームワーク。クラス名を HTML に直接記述することでスタイリングを行う。カスタム CSS を書く量を最小化し、デザインの一貫性を保ちやすい。バージョン 4 からは設定ファイルが不要になり、CSS ファイルに直接テーマを定義できる。

### Shadcn UI

Shadcn UI は Tailwind CSS ベースのコンポーネント集。npm パッケージとしてインストールするのではなく、`npx shadcn add` コマンドでソースコードを `components/ui/` にコピーする形式を取る。コピーしたファイルは直接編集してカスタマイズできる。

## コンポーネントの追加

```bash
npx shadcn add <component-name>
# 例: npx shadcn add dialog
```

追加されたコンポーネントは `components/ui/` に配置される。直接編集してカスタマイズしてよい。

## クラスの合成

条件付きクラスの適用には `cn()` ユーティリティを使う。内部で `clsx` と `tailwind-merge` を組み合わせており、クラスの競合を自動解決する。

```typescript
import { cn } from "@/lib/utils";

<div className={cn("base-class", isActive && "active-class", className)} />
```

## コンポーネントの使い方

```tsx
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

<Button variant="outline" size="sm">キャンセル</Button>
<Badge variant="destructive">キャンセル済</Badge>
```

各コンポーネントは `variant` や `size` などの props でスタイルを切り替えられる。使用可能な値は各コンポーネントのファイル（`components/ui/*.tsx`）内の `cva()` 定義を確認する。
