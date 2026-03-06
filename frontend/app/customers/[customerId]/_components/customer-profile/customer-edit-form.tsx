"use client";

import { useActionState } from "react";
import { useForm } from "@conform-to/react";
import { parseWithZod } from "@conform-to/zod/v4";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Customer } from "@/types/customer";
import { updateCustomer } from "../../_actions/update-customer";

const schema = z.object({
  name: z.string().min(1, "名前を入力してください"),
  email: z.string().email("有効なメールアドレスを入力してください"),
});

export function CustomerEditForm({
  customer,
  onCancel,
}: {
  customer: Customer;
  onCancel: () => void;
}) {
  const boundAction = updateCustomer.bind(null, customer.id);
  const [lastResult, action] = useActionState(boundAction, null);

  const [form, fields] = useForm({
    lastResult,
    defaultValue: { name: customer.name, email: customer.email },
    onValidate({ formData }) {
      return parseWithZod(formData, { schema });
    },
    shouldValidate: "onBlur",
    shouldRevalidate: "onInput",
  });

  return (
    <form id={form.id} onSubmit={form.onSubmit} action={action} noValidate>
      <div className="grid gap-4">
        <div className="grid gap-1.5">
          <Label htmlFor={fields.name.id}>名前</Label>
          <Input
            id={fields.name.id}
            name={fields.name.name}
            defaultValue={fields.name.initialValue}
            aria-invalid={!!fields.name.errors}
          />
          {fields.name.errors && (
            <p className="text-sm text-destructive">{fields.name.errors[0]}</p>
          )}
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor={fields.email.id}>メール</Label>
          <Input
            id={fields.email.id}
            name={fields.email.name}
            type="email"
            defaultValue={fields.email.initialValue}
            aria-invalid={!!fields.email.errors}
          />
          {fields.email.errors && (
            <p className="text-sm text-destructive">{fields.email.errors[0]}</p>
          )}
        </div>
        <div className="flex gap-2">
          <Button type="submit">保存</Button>
          <Button type="button" variant="outline" onClick={onCancel}>
            キャンセル
          </Button>
        </div>
      </div>
    </form>
  );
}
