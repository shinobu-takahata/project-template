import { getCustomer } from "../../_lib/fetcher";
import { CustomerProfile } from "./customer-profile";

export async function CustomerProfileContainer({ customerId }: { customerId: string }) {
  const customer = await getCustomer(customerId);
  return <CustomerProfile customer={customer} />;
}
