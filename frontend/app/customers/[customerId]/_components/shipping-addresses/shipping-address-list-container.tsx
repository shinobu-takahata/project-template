import { getCustomer } from "../../_lib/fetcher";
import { ShippingAddressList } from "./shipping-address-list";

export async function ShippingAddressListContainer({ customerId }: { customerId: string }) {
  const customer = await getCustomer(customerId);
  return <ShippingAddressList customerId={customerId} addresses={customer.shippingAddresses} />;
}
