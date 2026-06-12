export default function Spinner({ size = "md" }) {
  const dim = size === "lg" ? "h-12 w-12" : size === "sm" ? "h-4 w-4" : "h-6 w-6";
  return (
    <div className={`${dim} animate-spin rounded-full border-4 border-gray-200 border-t-brand-500`} />
  );
}
