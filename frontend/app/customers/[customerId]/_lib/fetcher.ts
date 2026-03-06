import "server-only";
import { cache } from "react";
import { apiClient } from "@/lib/api-client";
import type { Customer } from "@/types/customer";
import type { Order } from "@/types/order";

export const getCustomer = cache(async (id: string): Promise<Customer> => {
  return apiClient.get<Customer>(`/customers/${id}`, {
    next: { tags: [`customer-${id}`] },
  });
});

export const getCustomerOrders = cache(async (id: string): Promise<Order[]> => {
  const response = await apiClient.get<{ data: Order[] }>(`/customers/${id}/orders`, {
    next: { tags: [`customer-${id}-orders`] },
  });
  return response.data;
});
