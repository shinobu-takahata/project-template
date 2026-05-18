"use server";

import { parseWithZod } from "@conform-to/zod/v4";
import { redirect } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { createCustomerSchema as schema } from "../_schema";

export async function createCustomer(_prevState: unknown, formData: FormData) {
  const submission = parseWithZod(formData, { schema });
  if (submission.status !== "success") {
    return submission.reply();
  }

  const { customer_id } = await apiClient.post<{ customer_id: string }>(
    "/customers",
    submission.value,
  );
  redirect(`/customers/${customer_id}`);
}
