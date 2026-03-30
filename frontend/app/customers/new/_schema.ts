import { z } from "zod";

export const createCustomerSchema = z.object({
  name: z.string().min(1, "名前を入力してください"),
  email: z.string().email("有効なメールアドレスを入力してください"),
  shipping_address: z.object({
    label: z.string().min(1, "ラベルを入力してください"),
    postal_code: z.string().min(1, "郵便番号を入力してください"),
    prefecture: z.string().min(1, "都道府県を入力してください"),
    city: z.string().min(1, "市区町村を入力してください"),
    street: z.string().min(1, "番地を入力してください"),
  }),
});
