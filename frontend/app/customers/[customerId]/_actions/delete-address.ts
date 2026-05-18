"use server";

import { revalidateTag } from "next/cache";
import { apiClient } from "@/lib/api-client";

export async function deleteAddress(customerId: string, addressId: string): Promise<void> {
  await apiClient.delete(`/customers/${customerId}/addresses/${addressId}`);
  revalidateTag(`customer-${customerId}`, { expire: 0 });
}
