export function Avatar({ email, size = "" }: { email: string; size?: "" | "lg" | "xl" }) {
  return <div className={`avatar ${size}`}>{(email[0] ?? "?").toUpperCase()}</div>;
}
