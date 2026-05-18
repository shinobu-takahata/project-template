import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Customer } from "@/types/customer";
import { CustomerEditForm } from "../customer-edit-form";

jest.mock("../../../_actions/update-customer", () => ({
  updateCustomer: jest.fn(),
}));

const baseCustomer: Customer = {
  id: "cust-1",
  name: "山田太郎",
  email: "taro@example.com",
  memberRank: "SILVER",
  shippingAddresses: [],
};

describe("CustomerEditForm", () => {
  describe("初期値の表示", () => {
    it("顧客の name が初期値として表示される", () => {
      render(<CustomerEditForm customer={baseCustomer} onCancel={jest.fn()} />);
      expect(screen.getByLabelText("名前")).toHaveValue("山田太郎");
    });

    it("顧客の email が初期値として表示される", () => {
      render(<CustomerEditForm customer={baseCustomer} onCancel={jest.fn()} />);
      expect(screen.getByLabelText("メール")).toHaveValue("taro@example.com");
    });
  });

  describe("onBlur バリデーション", () => {
    it("name を空にしてフォーカスアウトすると invalid になる", async () => {
      const user = userEvent.setup();
      render(<CustomerEditForm customer={baseCustomer} onCancel={jest.fn()} />);

      const nameInput = screen.getByLabelText("名前");
      await user.clear(nameInput);
      await user.tab();

      expect(nameInput).toHaveAttribute("aria-invalid", "true");
    });

    it("email に不正なフォーマットを入力してフォーカスアウトするとエラーメッセージが表示される", async () => {
      const user = userEvent.setup();
      render(<CustomerEditForm customer={baseCustomer} onCancel={jest.fn()} />);

      const emailInput = screen.getByLabelText("メール");
      await user.clear(emailInput);
      await user.type(emailInput, "not-an-email");
      await user.tab();

      expect(screen.getByText("有効なメールアドレスを入力してください")).toBeInTheDocument();
    });
  });

  describe("キャンセルボタン", () => {
    it("キャンセルボタンをクリックすると onCancel が呼ばれる", async () => {
      const user = userEvent.setup();
      const onCancel = jest.fn();
      render(<CustomerEditForm customer={baseCustomer} onCancel={onCancel} />);

      await user.click(screen.getByRole("button", { name: "キャンセル" }));

      expect(onCancel).toHaveBeenCalledTimes(1);
    });
  });
});
