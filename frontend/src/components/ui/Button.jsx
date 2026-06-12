import Spinner from "./Spinner";

export default function Button({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  className = "",
  ...props
}) {
  const base = "inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-400 disabled:opacity-50 disabled:cursor-not-allowed";
  const sizes = { sm: "px-3 py-1.5 text-sm", md: "px-4 py-2 text-sm", lg: "px-6 py-3 text-base" };
  const variants = {
    // Light gray primary with a soft teal accent border on hover
    primary:  "bg-gray-100 text-gray-800 border border-gray-300 shadow-soft hover:bg-gray-200 hover:border-brand-300",
    secondary:"bg-white text-gray-600 border border-gray-200 hover:bg-gray-50 hover:text-gray-900",
    // Solid teal accent — reserved for the single strongest call-to-action
    accent:   "bg-brand-500 text-white hover:bg-brand-600 shadow-soft",
    danger:   "bg-red-50 text-red-700 border border-red-200 hover:bg-red-100",
    ghost:    "text-gray-600 hover:bg-gray-100",
  };

  return (
    <button
      className={`${base} ${sizes[size]} ${variants[variant] ?? variants.primary} ${className}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  );
}
