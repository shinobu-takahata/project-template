import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { Order } from "@/types/order";
import { OrderHistoryItem } from "./order-history-item";

export function OrderHistoryList({ orders }: { orders: Order[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>注文履歴</CardTitle>
      </CardHeader>
      <Separator />
      <CardContent className="pt-6">
        {orders.length === 0 ? (
          <p className="text-sm text-muted-foreground">注文履歴がありません。</p>
        ) : (
          <div className="grid gap-4">
            {orders.map((order) => (
              <OrderHistoryItem key={order.id} order={order} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
