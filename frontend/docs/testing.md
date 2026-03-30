# テスト

## テストフェーズと対象

| フェーズ | 対象 | ツール | 状態 |
|---|---|---|---|
| 単体テスト | Client Component の操作 / Zod スキーマ検証 | Jest + React Testing Library | 実装済 |
| 結合テスト | Server Action〜API連携 / エラーレスポンスの表示 | Jest + MSW | 未実装 |
| システムテスト | ユーザーシナリオ全体 | Playwright | 未実装 |

## 単体テストの対象

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

## セットアップ

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

## テストファイルの配置

対象コンポーネントと同じディレクトリに `__tests__/` を作成し、その中に配置する。

```
_components/
  customer-profile/
    customer-edit-form.tsx
    __tests__/
      customer-edit-form.test.tsx   ← ここに配置
```

## モックパターン

### Server Action のモック

```tsx
// テストファイルの先頭（import の前）
jest.mock("../../../_actions/update-customer", () => ({
  updateCustomer: jest.fn(),
}));
```

パスは**テストファイルから見た相対パス**で指定する。

### 子コンポーネントのモック

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

## クエリの選び方（優先順）

| 優先度 | クエリ | 使うとき |
|---|---|---|
| 1 | `getByRole` | ボタン、テキストボックス、チェックボックスなど |
| 2 | `getByLabelText` | `<label>` と紐づいた入力要素 |
| 3 | `getByText` | 表示テキストで探す |
| 4 | `getByTestId` | モックコンポーネント内など（最終手段） |

## コード例

### パターン1: Zod スキーマのテスト

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

### パターン2: 表示テスト（静的）

```tsx
import { render, screen } from "@testing-library/react";
import { ShippingAddressCard } from "../shipping-address-card";

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

### パターン3: インタラクションテスト（userEvent）

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

### パターン4: フォームバリデーションテスト

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

### パターン5: コールバック呼び出しテスト

```tsx
it("キャンセルボタンをクリックすると onCancel が呼ばれる", async () => {
  const user = userEvent.setup();
  const onCancel = jest.fn();
  render(<CustomerEditForm customer={baseCustomer} onCancel={onCancel} />);

  await user.click(screen.getByRole("button", { name: "キャンセル" }));

  expect(onCancel).toHaveBeenCalledTimes(1);
});
```

## 既知の注意事項

### conform + Zod v4 の空フィールドの挙動

空フィールドは `undefined` に変換されるため、空値バリデーションは `aria-invalid` 属性で確認する。詳細は [conform-zod.md](./conform-zod.md) を参照。

### Server Action のモック

`"use server"` ファイルは `jest.mock()` でモックする。`next/cache` などの依存も自動的にモックされる。
