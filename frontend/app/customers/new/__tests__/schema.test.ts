import { createCustomerSchema } from "../_schema";

const validInput = {
  name: "山田太郎",
  email: "taro@example.com",
  shipping_address: {
    label: "自宅",
    postal_code: "100-0001",
    prefecture: "東京都",
    city: "千代田区",
    street: "千代田1-1-1",
  },
};

describe("createCustomerSchema", () => {
  describe("正常系", () => {
    it("全フィールド有効値でバリデーション成功", () => {
      const result = createCustomerSchema.safeParse(validInput);
      expect(result.success).toBe(true);
    });
  });

  describe("name", () => {
    it("空文字のとき失敗", () => {
      const result = createCustomerSchema.safeParse({ ...validInput, name: "" });
      expect(result.success).toBe(false);
      if (!result.success) {
        const nameErrors = result.error.issues.filter((i) => i.path.includes("name"));
        expect(nameErrors.length).toBeGreaterThan(0);
        expect(nameErrors[0].message).toBe("名前を入力してください");
      }
    });
  });

  describe("email", () => {
    it("空文字のとき失敗", () => {
      const result = createCustomerSchema.safeParse({ ...validInput, email: "" });
      expect(result.success).toBe(false);
    });

    it("不正なフォーマットのとき失敗", () => {
      const result = createCustomerSchema.safeParse({
        ...validInput,
        email: "not-an-email",
      });
      expect(result.success).toBe(false);
      if (!result.success) {
        const emailErrors = result.error.issues.filter((i) => i.path.includes("email"));
        expect(emailErrors.length).toBeGreaterThan(0);
        expect(emailErrors[0].message).toBe("有効なメールアドレスを入力してください");
      }
    });
  });

  describe("shipping_address", () => {
    it("shipping_address 自体が欠損のとき失敗", () => {
      const { shipping_address: _, ...rest } = validInput;
      const result = createCustomerSchema.safeParse(rest);
      expect(result.success).toBe(false);
    });

    const addressFields = [
      { field: "label", message: "ラベルを入力してください" },
      { field: "postal_code", message: "郵便番号を入力してください" },
      { field: "prefecture", message: "都道府県を入力してください" },
      { field: "city", message: "市区町村を入力してください" },
      { field: "street", message: "番地を入力してください" },
    ] as const;

    addressFields.forEach(({ field, message }) => {
      it(`${field} が空文字のとき失敗`, () => {
        const result = createCustomerSchema.safeParse({
          ...validInput,
          shipping_address: { ...validInput.shipping_address, [field]: "" },
        });
        expect(result.success).toBe(false);
        if (!result.success) {
          const errors = result.error.issues.filter((i) => i.path.includes(field));
          expect(errors.length).toBeGreaterThan(0);
          expect(errors[0].message).toBe(message);
        }
      });
    });
  });
});
