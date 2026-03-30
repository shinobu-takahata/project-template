export type OrderStatus =
  | "CONFIRMED"
  | "PAID"
  | "PREPARING"
  | "SHIPPED"
  | "DELIVERED"
  | "CANCELLED";

export type OrderItem = {
  id: string;
  productName: string;
  quantity: number;
  unitPrice: number;
};

export type Order = {
  id: string;
  status: OrderStatus;
  totalAmount: number;
  createdAt: string;
  items: OrderItem[];
};
