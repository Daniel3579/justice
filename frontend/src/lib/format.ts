export function pluralChats(n: number): string {
  const a = n % 10, b = n % 100;
  if (a === 1 && b !== 11) return "чат";
  if (a >= 2 && a <= 4 && (b < 12 || b > 14)) return "чата";
  return "чатов";
}

export function formatDate(iso: string): string {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? "" : d.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });
}

export function downloadBlob(blob: Blob, name: string) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
