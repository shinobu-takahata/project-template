"use client";

import { useActionState } from "react";
import { useForm } from "@conform-to/react";
import { parseWithZod } from "@conform-to/zod/v4";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createCustomer } from "../_actions/create-customer";
import { createCustomerSchema as schema } from "../_schema";

export function CustomerNewForm() {
  const [lastResult, action] = useActionState(createCustomer, null);

  const [form, fields] = useForm({
    lastResult,
    onValidate({ formData }) {
      return parseWithZod(formData, { schema });
    },
    shouldValidate: "onBlur",
    shouldRevalidate: "onInput",
  });

  const shippingAddress = fields.shipping_address.getFieldset();

  return (
    <form id={form.id} onSubmit={form.onSubmit} action={action} noValidate>
      <div className="grid gap-4">
        <div className="grid gap-1.5">
          <Label htmlFor={fields.name.id}>名前</Label>
          <Input
            id={fields.name.id}
            name={fields.name.name}
            aria-invalid={!!fields.name.errors}
          />
          {fields.name.errors && (
            <p className="text-sm text-destructive">{fields.name.errors[0]}</p>
          )}
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor={fields.email.id}>メールアドレス</Label>
          <Input
            id={fields.email.id}
            name={fields.email.name}
            type="email"
            aria-invalid={!!fields.email.errors}
          />
          {fields.email.errors && (
            <p className="text-sm text-destructive">{fields.email.errors[0]}</p>
          )}
        </div>

        <p className="text-sm font-medium">デフォルト配送先住所</p>
        <div className="grid gap-1.5">
          <Label htmlFor={shippingAddress.label.id}>ラベル</Label>
          <Input
            id={shippingAddress.label.id}
            name={shippingAddress.label.name}
            placeholder="自宅"
            aria-invalid={!!shippingAddress.label.errors}
          />
          {shippingAddress.label.errors && (
            <p className="text-sm text-destructive">{shippingAddress.label.errors[0]}</p>
          )}
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor={shippingAddress.postal_code.id}>郵便番号</Label>
          <Input
            id={shippingAddress.postal_code.id}
            name={shippingAddress.postal_code.name}
            placeholder="100-0001"
            aria-invalid={!!shippingAddress.postal_code.errors}
          />
          {shippingAddress.postal_code.errors && (
            <p className="text-sm text-destructive">{shippingAddress.postal_code.errors[0]}</p>
          )}
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor={shippingAddress.prefecture.id}>都道府県</Label>
          <Input
            id={shippingAddress.prefecture.id}
            name={shippingAddress.prefecture.name}
            placeholder="東京都"
            aria-invalid={!!shippingAddress.prefecture.errors}
          />
          {shippingAddress.prefecture.errors && (
            <p className="text-sm text-destructive">{shippingAddress.prefecture.errors[0]}</p>
          )}
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor={shippingAddress.city.id}>市区町村</Label>
          <Input
            id={shippingAddress.city.id}
            name={shippingAddress.city.name}
            placeholder="千代田区"
            aria-invalid={!!shippingAddress.city.errors}
          />
          {shippingAddress.city.errors && (
            <p className="text-sm text-destructive">{shippingAddress.city.errors[0]}</p>
          )}
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor={shippingAddress.street.id}>番地・建物名</Label>
          <Input
            id={shippingAddress.street.id}
            name={shippingAddress.street.name}
            placeholder="千代田1-1-1"
            aria-invalid={!!shippingAddress.street.errors}
          />
          {shippingAddress.street.errors && (
            <p className="text-sm text-destructive">{shippingAddress.street.errors[0]}</p>
          )}
        </div>

        <Button type="submit" className="w-full">
          登録
        </Button>
      </div>
    </form>
  );
}
