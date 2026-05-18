"use server";

import { parseWithZod } from "@conform-to/zod/v4";
import { revalidateTag } from "next/cache";
import { z } from "zod";
import { apiClient } from "@/lib/api-client";

const schema = z.object({
  postalCode: z.string().min(1, "郵便番号を入力してください"),
  prefecture: z.string().min(1, "都道府県を入力してください"),
  city: z.string().min(1, "市区町村を入力してください"),
  street: z.string().min(1, "番地・建物名を入力してください"),
  isDefault: z
    .string()
    .optional()
    .transform((v) => v === "on"),
});

export async function addAddress(customerId: string, _prevState: unknown, formData: FormData) {
  const submission = parseWithZod(formData, { schema });
  if (submission.status !== "success") {
    return submission.reply();
  }

  await apiClient.post(`/customers/${customerId}/addresses`, submission.value);
  revalidateTag(`customer-${customerId}`, { expire: 0 });

  return submission.reply();
}
