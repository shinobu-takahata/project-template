# @conform-to/react + Zod v4

## 概要

### Zod

Zod はスキーマ定義とバリデーションのためのライブラリ。TypeScript ファーストで設計されており、スキーマから型を自動推論できる。サーバー（Server Action）とクライアント（フォームコンポーネント）の両側で同じスキーマを共有することで、バリデーションの一貫性を保つ。

### @conform-to/react

conform は React の `useActionState` と連携するフォーム状態管理ライブラリ。フィールドの ID・name・エラー状態を管理し、アクセシビリティ属性（`aria-invalid` など）の付与を自動化する。Progressive Enhancement（JS なし環境でも動作）を前提とした設計になっている。

### @conform-to/zod

conform と Zod を連携させるアダプター。`parseWithZod()` でフォームデータをパースし、バリデーションエラーを conform のフォーマットに変換する。

## 基本的な使い方

フォーム状態管理は `useActionState` + `useForm` の組み合わせで行う。

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
        aria-invalid={!!fields.name.errors}
      />
      {fields.name.errors && (
        <p>{fields.name.errors[0]}</p>
      )}
    </form>
  );
}
```

## 注意事項：空フィールドの挙動

`@conform-to/zod/v4` は空のフォームフィールドを `""` ではなく `undefined` に変換する。
そのため `z.string().min(1, "メッセージ")` のカスタムメッセージは空値には適用されない。

| 値 | Zod の挙動 |
|---|---|
| `"invalid@"` | `z.string().email(...)` → カスタムメッセージが表示される |
| `""` (空入力) | conform が `undefined` に変換 → 型エラーメッセージが表示される |

テストで空フィールドのバリデーション失敗を確認するときは `aria-invalid` 属性を使う。

```tsx
// NG: 空値に対しカスタムメッセージは表示されない
expect(screen.getByText("名前を入力してください")).toBeInTheDocument();

// OK: aria-invalid でバリデーション失敗を確認する
expect(screen.getByLabelText("名前")).toHaveAttribute("aria-invalid", "true");
```

## ネストされたオブジェクト

住所フォームなど、ネストされたオブジェクトフィールドを扱う場合は `getFieldset()` を使う。

```tsx
const shippingAddress = fields.shipping_address.getFieldset();

<input name={shippingAddress.postal_code.name} />
// name 属性値: "shipping_address.postal_code"
```
