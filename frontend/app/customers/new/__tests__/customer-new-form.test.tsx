import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CustomerNewForm } from "../_components/customer-new-form";

// NOTE: @conform-to/zod/v4 は空文字を undefined に変換するため、
//       空フィールドのエラーは型チェック (z.string()) で弾かれる。
//       カスタムメッセージ ("名前を入力してください") は空文字の場合に表示される。
//       空フィールドのバリデーション確認は aria-invalid 属性で行う。

jest.mock("../_actions/create-customer", () => ({
  createCustomer: jest.fn(),
}));

describe("CustomerNewForm", () => {
  describe("フォーム送信時のバリデーション", () => {
    it("全フィールド未入力で送信すると name フィールドが invalid になる", async () => {
      const user = userEvent.setup();
      render(<CustomerNewForm />);

      await user.click(screen.getByRole("button", { name: "登録" }));

      expect(screen.getByLabelText("名前")).toHaveAttribute("aria-invalid", "true");
    });

    it("全フィールド未入力で送信すると email フィールドが invalid になる", async () => {
      const user = userEvent.setup();
      render(<CustomerNewForm />);

      await user.click(screen.getByRole("button", { name: "登録" }));

      expect(screen.getByLabelText("メールアドレス")).toHaveAttribute("aria-invalid", "true");
    });

    it("全フィールド未入力で送信すると住所フィールドが invalid になる", async () => {
      const user = userEvent.setup();
      render(<CustomerNewForm />);

      await user.click(screen.getByRole("button", { name: "登録" }));

      expect(screen.getByLabelText("郵便番号")).toHaveAttribute("aria-invalid", "true");
      expect(screen.getByLabelText("都道府県")).toHaveAttribute("aria-invalid", "true");
      expect(screen.getByLabelText("市区町村")).toHaveAttribute("aria-invalid", "true");
    });
  });

  describe("個別フィールドの onBlur バリデーション", () => {
    it("name フィールドを空のままフォーカスアウトすると invalid になる", async () => {
      const user = userEvent.setup();
      render(<CustomerNewForm />);

      await user.click(screen.getByLabelText("名前"));
      await user.tab();

      expect(screen.getByLabelText("名前")).toHaveAttribute("aria-invalid", "true");
    });

    it("email に不正なフォーマットを入力してフォーカスアウトするとエラーメッセージが表示される", async () => {
      const user = userEvent.setup();
      render(<CustomerNewForm />);

      await user.type(screen.getByLabelText("メールアドレス"), "not-an-email");
      await user.tab();

      expect(screen.getByText("有効なメールアドレスを入力してください")).toBeInTheDocument();
    });
  });
});
