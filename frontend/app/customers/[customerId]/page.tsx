import { Suspense } from "react";
import { CustomerProfileContainer } from "./_components/customer-profile/customer-profile-container";
import { ShippingAddressListContainer } from "./_components/shipping-addresses/shipping-address-list-container";
import { OrderHistoryContainer } from "./_components/order-history/order-history-container";
import { OrderHistorySkeleton } from "./_components/order-history/order-history-skeleton";

export default async function CustomerDetailPage({
  params,
}: {
  params: Promise<{ customerId: string }>;
}) {
  const { customerId } = await params;

  return (
    <div className="grid gap-6">
      <CustomerProfileContainer customerId={customerId} />
      <ShippingAddressListContainer customerId={customerId} />
      <Suspense fallback={<OrderHistorySkeleton />}>
        <OrderHistoryContainer customerId={customerId} />
      </Suspense>
    </div>
  );
}
