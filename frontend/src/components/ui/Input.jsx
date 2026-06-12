export default function Input({ label, error, className = "", ...props }) {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-sm font-medium text-gray-700">{label}</label>}
      <input
        className={`rounded-lg border px-3 py-2 text-sm shadow-soft focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-400 ${
          error ? "border-red-500" : "border-gray-300"
        } ${className}`}
        {...props}
      />
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
