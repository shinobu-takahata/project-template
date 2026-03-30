export const dynamic = "force-dynamic";

import Link from "next/link";
import { Plus } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { Customer, MemberRank } from "@/types/customer";

const RANK_LABELS: Record<MemberRank, string> = {
  BRONZE: "ブロンズ",
  SILVER: "シルバー",
  GOLD: "ゴールド",
};

async function getCustomers(): Promise<Customer[]> {
  try {
    return await apiClient.get<Customer[]>("/customers");
  } catch {
    return [];
  }
}

export default async function CustomersPage() {
  const customers = await getCustomers();

  return (
    <div className="grid gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">顧客一覧</h2>
        <Button asChild>
          <Link href="/customers/new">
            <Plus className="mr-1 h-4 w-4" />
            新規登録
          </Link>
        </Button>
      </div>
      {customers.length === 0 ? (
        <p className="text-sm text-muted-foreground">顧客が登録されていません。</p>
      ) : (
        <div className="grid gap-3">
          {customers.map((customer) => (
            <Link key={customer.id} href={`/customers/${customer.id}`}>
              <Card className="transition-colors hover:bg-muted/50">
                <CardContent className="flex items-center justify-between py-4">
                  <div>
                    <p className="font-medium">{customer.name}</p>
                    <p className="text-sm text-muted-foreground">{customer.email}</p>
                  </div>
                  <Badge variant="outline">
                    {RANK_LABELS[customer.memberRank]}
                  </Badge>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
