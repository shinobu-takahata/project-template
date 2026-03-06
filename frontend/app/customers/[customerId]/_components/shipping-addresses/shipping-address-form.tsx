"use client";

import { useActionState } from "react";
import { useForm } from "@conform-to/react";
import { parseWithZod } from "@conform-to/zod/v4";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ShippingAddress } from "@/types/customer";
import { addAddress } from "../../_actions/add-address";
import { updateAddress } from "../../_actions/update-address";

const schema = z.object({
  postalCode: z.string().min(1, "郵便番号を入力してください"),
  prefecture: z.string().min(1, "都道府県を入力してください"),
  city: z.string().min(1, "市区町村を入力してください"),
  street: z.string().min(1, "番地・建物名を入力してください"),
  isDefault: z
    .string()
    .optional()
    .transform((v) => v === "on"),
});

type Props =
  | { customerId: string; mode: "add"; address?: undefined; onCancel: () => void }
  | { customerId: string; mode: "edit"; address: ShippingAddress; onCancel: () => void };

export function ShippingAddressForm({ customerId, mode, address, onCancel }: Props) {
  const boundAction =
    mode === "add"
      ? addAddress.bind(null, customerId)
      : updateAddress.bind(null, customerId, address!.id);

  const [lastResult, action] = useActionState(boundAction, null);

  const [form, fields] = useForm({
    lastResult,
    defaultValue:
      mode === "edit"
        ? {
            postalCode: address!.address.postalCode,
            prefecture: address!.address.prefecture,
            city: address!.address.city,
            street: address!.address.street,
            isDefault: address!.isDefault ? "on" : undefined,
          }
        : undefined,
    onValidate({ formData }) {
      return parseWithZod(formData, { schema });
    },
    shouldValidate: "onBlur",
    shouldRevalidate: "onInput",
  });

  return (
    <form
      id={form.id}
      onSubmit={form.onSubmit}
      action={action}
      noValidate
      className="rounded-lg border p-4"
    >
      <h3 className="mb-4 text-sm font-semibold">
        {mode === "add" ? "住所を追加" : "住所を編集"}
      </h3>
      <div className="grid gap-4">
        <div className="grid gap-1.5">
          <Label htmlFor={fields.postalCode.id}>郵便番号</Label>
          <Input
            id={fields.postalCode.id}
            name={fields.postalCode.name}
            defaultValue={fields.postalCode.initialValue}
            placeholder="1234567"
          />
          {fields.postalCode.errors && (
            <p className="text-sm text-destructive">{fields.postalCode.errors[0]}</p>
          )}
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor={fields.prefecture.id}>都道府県</Label>
          <Input
            id={fields.prefecture.id}
            name={fields.prefecture.name}
            defaultValue={fields.prefecture.initialValue}
          />
          {fields.prefecture.errors && (
            <p className="text-sm text-destructive">{fields.prefecture.errors[0]}</p>
          )}
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor={fields.city.id}>市区町村</Label>
          <Input
            id={fields.city.id}
            name={fields.city.name}
            defaultValue={fields.city.initialValue}
          />
          {fields.city.errors && (
            <p className="text-sm text-destructive">{fields.city.errors[0]}</p>
          )}
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor={fields.street.id}>番地・建物名</Label>
          <Input
            id={fields.street.id}
            name={fields.street.name}
            defaultValue={fields.street.initialValue}
          />
          {fields.street.errors && (
            <p className="text-sm text-destructive">{fields.street.errors[0]}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <input
            id={fields.isDefault.id}
            name={fields.isDefault.name}
            type="checkbox"
            defaultChecked={fields.isDefault.initialValue === "on"}
          />
          <Label htmlFor={fields.isDefault.id}>デフォルト住所に設定</Label>
        </div>
        <div className="flex gap-2">
          <Button type="submit">{mode === "add" ? "追加" : "保存"}</Button>
          <Button type="button" variant="outline" onClick={onCancel}>
            キャンセル
          </Button>
        </div>
      </div>
    </form>
  );
}
