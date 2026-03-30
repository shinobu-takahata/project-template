import { getCustomerOrders } from "../../_lib/fetcher";
import { OrderHistoryList } from "./order-history-list";

export async function OrderHistoryContainer({
  customerId,
}: {
  customerId: string;
}) {
  const orders = await getCustomerOrders(customerId);
  return <OrderHistoryList orders={orders} />;
}
