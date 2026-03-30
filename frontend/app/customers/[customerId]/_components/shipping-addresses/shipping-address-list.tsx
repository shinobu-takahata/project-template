"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { ShippingAddress } from "@/types/customer";
import { ShippingAddressCard } from "./shipping-address-card";
import { ShippingAddressForm } from "./shipping-address-form";

export function ShippingAddressList({
  customerId,
  addresses,
}: {
  customerId: string;
  addresses: ShippingAddress[];
}) {
  const [isAdding, setIsAdding] = useState(false);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>配送先住所</CardTitle>
        {!isAdding && addresses.length < 5 && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsAdding(true)}
          >
            <Plus className="mr-1 h-4 w-4" />
            住所を追加
          </Button>
        )}
      </CardHeader>
      <Separator />
      <CardContent className="pt-6">
        {isAdding && (
          <div className="mb-4">
            <ShippingAddressForm
              customerId={customerId}
              mode="add"
              onCancel={() => setIsAdding(false)}
            />
          </div>
        )}
        {addresses.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            配送先住所が登録されていません。
          </p>
        ) : (
          <div className="grid gap-4">
            {addresses.map((address) => (
              <ShippingAddressCard
                key={address.id}
                customerId={customerId}
                address={address}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
