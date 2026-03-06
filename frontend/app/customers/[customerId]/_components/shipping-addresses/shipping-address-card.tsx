"use client";

import { useState } from "react";
import { Pencil, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ShippingAddress } from "@/types/customer";
import { deleteAddress } from "../../_actions/delete-address";
import { ShippingAddressForm } from "./shipping-address-form";

export function ShippingAddressCard({
  customerId,
  address,
}: {
  customerId: string;
  address: ShippingAddress;
}) {
  const [isEditing, setIsEditing] = useState(false);

  if (isEditing) {
    return (
      <ShippingAddressForm
        customerId={customerId}
        mode="edit"
        address={address}
        onCancel={() => setIsEditing(false)}
      />
    );
  }

  const { postalCode, prefecture, city, street } = address.address;

  return (
    <div className="rounded-lg border p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="text-sm">
          <p className="text-muted-foreground">〒{postalCode}</p>
          <p className="font-medium">
            {prefecture}{city}{street}
          </p>
          {address.isDefault && (
            <Badge variant="secondary" className="mt-1">
              デフォルト住所
            </Badge>
          )}
        </div>
        <div className="flex shrink-0 gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsEditing(true)}
            aria-label="編集"
          >
            <Pencil className="h-4 w-4" />
          </Button>
          <form
            action={deleteAddress.bind(null, customerId, address.id)}
          >
            <Button
              type="submit"
              variant="ghost"
              size="icon"
              aria-label="削除"
            >
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
