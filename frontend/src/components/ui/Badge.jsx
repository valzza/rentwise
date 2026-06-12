const colors = {
  green:  "bg-brand-100 text-brand-700",
  red:    "bg-red-100 text-red-800",
  yellow: "bg-amber-100 text-amber-800",
  blue:   "bg-brand-100 text-brand-700",
  teal:   "bg-brand-100 text-brand-700",
  gray:   "bg-gray-100 text-gray-600",
};

export default function Badge({ children, color = "gray" }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[color]}`}>
      {children}
    </span>
  );
}
