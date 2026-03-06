import Link from "next/link";

export default function CustomerNotFound() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16">
      <h2 className="text-xl font-semibold">顧客が見つかりません</h2>
      <p className="text-muted-foreground">
        指定された顧客は存在しないか、削除された可能性があります。
      </p>
      <Link
        href="/customers"
        className="rounded bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90"
      >
        顧客一覧へ戻る
      </Link>
    </div>
  );
}
