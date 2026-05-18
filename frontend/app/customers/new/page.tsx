import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CustomerNewForm } from "./_components/customer-new-form";

export default function CustomerNewPage() {
  return (
    <div className="grid gap-4">
      <Link
        href="/customers"
        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        顧客一覧へ戻る
      </Link>
      <Card className="max-w-md">
        <CardHeader>
          <CardTitle>顧客新規登録</CardTitle>
        </CardHeader>
        <CardContent>
          <CustomerNewForm />
        </CardContent>
      </Card>
    </div>
  );
}
