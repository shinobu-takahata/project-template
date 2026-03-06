"use client";

export default function CustomerDetailError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16">
      <h2 className="text-xl font-semibold">エラーが発生しました</h2>
      <p className="text-muted-foreground">{error.message}</p>
      <button
        onClick={reset}
        className="rounded bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90"
      >
        再試行
      </button>
    </div>
  );
}
