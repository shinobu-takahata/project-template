export type MemberRank = "BRONZE" | "SILVER" | "GOLD";

export type Address = {
  postalCode: string;
  prefecture: string;
  city: string;
  street: string;
};

export type ShippingAddress = {
  id: string;
  address: Address;
  isDefault: boolean;
};

export type Customer = {
  id: string;
  name: string;
  email: string;
  memberRank: MemberRank;
  shippingAddresses: ShippingAddress[];
};
