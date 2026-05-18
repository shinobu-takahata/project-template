"use server";

import { parseWithZod } from "@conform-to/zod/v4";
import { revalidateTag } from "next/cache";
import { z } from "zod";
import { apiClient } from "@/lib/api-client";

const schema = z.object({
  name: z.string().min(1, "名前を入力してください"),
  email: z.string().email("有効なメールアドレスを入力してください"),
});

export async function updateCustomer(customerId: string, _prevState: unknown, formData: FormData) {
  const submission = parseWithZod(formData, { schema });
  if (submission.status !== "success") {
    return submission.reply();
  }

  await apiClient.put(`/customers/${customerId}`, submission.value);
  revalidateTag(`customer-${customerId}`, { expire: 0 });

  return submission.reply();
}
