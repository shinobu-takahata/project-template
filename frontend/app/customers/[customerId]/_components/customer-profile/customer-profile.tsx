"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { Customer, MemberRank } from "@/types/customer";
import { CustomerEditForm } from "./customer-edit-form";

const RANK_LABELS: Record<MemberRank, string> = {
  BRONZE: "ブロンズ",
  SILVER: "シルバー",
  GOLD: "ゴールド",
};

const RANK_VARIANTS: Record<MemberRank, "default" | "secondary" | "outline"> = {
  BRONZE: "outline",
  SILVER: "secondary",
  GOLD: "default",
};

export function CustomerProfile({ customer }: { customer: Customer }) {
  const [isEditing, setIsEditing] = useState(false);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>顧客情報</CardTitle>
        {!isEditing && (
          <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
            編集
          </Button>
        )}
      </CardHeader>
      <Separator />
      <CardContent className="pt-6">
        {isEditing ? (
          <CustomerEditForm customer={customer} onCancel={() => setIsEditing(false)} />
        ) : (
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-3 text-sm">
            <dt className="font-medium text-muted-foreground">名前</dt>
            <dd>{customer.name}</dd>
            <dt className="font-medium text-muted-foreground">メール</dt>
            <dd>{customer.email}</dd>
            <dt className="font-medium text-muted-foreground">会員ランク</dt>
            <dd>
              <Badge variant={RANK_VARIANTS[customer.memberRank]}>
                {RANK_LABELS[customer.memberRank]}
              </Badge>
            </dd>
          </dl>
        )}
      </CardContent>
    </Card>
  );
}
