import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ShippingAddress } from "@/types/customer";
import { ShippingAddressCard } from "../shipping-address-card";

jest.mock("../../../_actions/delete-address", () => ({
  deleteAddress: jest.fn(),
}));

jest.mock("../shipping-address-form", () => ({
  ShippingAddressForm: ({ onCancel }: { onCancel: () => void }) => (
    <div data-testid="shipping-address-form">
      <button type="button" onClick={onCancel}>フォームキャンセル</button>
    </div>
  ),
}));

const baseAddress: ShippingAddress = {
  id: "addr-1",
  address: {
    postalCode: "100-0001",
    prefecture: "東京都",
    city: "千代田区",
    street: "千代田1-1-1",
  },
  isDefault: false,
};

describe("ShippingAddressCard", () => {
  describe("住所情報の表示", () => {
    it("郵便番号が表示される", () => {
      render(<ShippingAddressCard customerId="cust-1" address={baseAddress} />);
      expect(screen.getByText("〒100-0001")).toBeInTheDocument();
    });

    it("都道府県・市区町村・番地が表示される", () => {
      render(<ShippingAddressCard customerId="cust-1" address={baseAddress} />);
      expect(screen.getByText("東京都千代田区千代田1-1-1")).toBeInTheDocument();
    });

    it("isDefault が false のとき「デフォルト住所」バッジが表示されない", () => {
      render(<ShippingAddressCard customerId="cust-1" address={baseAddress} />);
      expect(screen.queryByText("デフォルト住所")).not.toBeInTheDocument();
    });

    it("isDefault が true のとき「デフォルト住所」バッジが表示される", () => {
      render(
        <ShippingAddressCard customerId="cust-1" address={{ ...baseAddress, isDefault: true }} />,
      );
      expect(screen.getByText("デフォルト住所")).toBeInTheDocument();
    });
  });

  describe("編集モードの切り替え", () => {
    it("編集ボタンをクリックすると ShippingAddressForm が表示される", async () => {
      const user = userEvent.setup();
      render(<ShippingAddressCard customerId="cust-1" address={baseAddress} />);

      await user.click(screen.getByRole("button", { name: "編集" }));

      expect(screen.getByTestId("shipping-address-form")).toBeInTheDocument();
    });

    it("編集モード中は住所カードが表示されない", async () => {
      const user = userEvent.setup();
      render(<ShippingAddressCard customerId="cust-1" address={baseAddress} />);

      await user.click(screen.getByRole("button", { name: "編集" }));

      expect(screen.queryByText("〒100-0001")).not.toBeInTheDocument();
    });

    it("フォームでキャンセルすると住所カード表示に戻る", async () => {
      const user = userEvent.setup();
      render(<ShippingAddressCard customerId="cust-1" address={baseAddress} />);

      await user.click(screen.getByRole("button", { name: "編集" }));
      expect(screen.getByTestId("shipping-address-form")).toBeInTheDocument();

      await user.click(screen.getByRole("button", { name: "フォームキャンセル" }));

      expect(screen.queryByTestId("shipping-address-form")).not.toBeInTheDocument();
      expect(screen.getByText("〒100-0001")).toBeInTheDocument();
    });
  });
});
