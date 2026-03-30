import { Badge } from "@/components/ui/badge";
import type { Order, OrderStatus } from "@/types/order";

const STATUS_LABELS: Record<OrderStatus, string> = {
  CONFIRMED: "注文確定",
  PAID: "支払済",
  PREPARING: "準備中",
  SHIPPED: "発送済",
  DELIVERED: "配達完了",
  CANCELLED: "キャンセル",
};

const STATUS_VARIANTS: Record<
  OrderStatus,
  "default" | "secondary" | "outline" | "destructive"
> = {
  CONFIRMED: "secondary",
  PAID: "secondary",
  PREPARING: "default",
  SHIPPED: "default",
  DELIVERED: "outline",
  CANCELLED: "destructive",
};

export function OrderHistoryItem({ order }: { order: Order }) {
  const createdAt = new Date(order.createdAt).toLocaleDateString("ja-JP");

  return (
    <div className="rounded-lg border p-4">
      <div className="flex items-center justify-between gap-2">
        <div>
          <p className="text-sm font-medium">注文 #{order.id}</p>
          <p className="text-xs text-muted-foreground">{createdAt}</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={STATUS_VARIANTS[order.status]}>
            {STATUS_LABELS[order.status]}
          </Badge>
          <p className="text-sm font-semibold">
            ¥{order.totalAmount.toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
}
