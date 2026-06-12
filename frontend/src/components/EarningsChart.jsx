// Lazy-loaded — only imports recharts (vendor-charts chunk) when this component mounts
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function EarningsChart({ data = [] }) {
  if (data.length === 0) {
    return <p className="text-sm text-gray-500 py-8 text-center">No earnings data yet.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="month" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `$${v}`} />
        <Tooltip formatter={(v) => [`$${v}`, "Revenue"]} />
        <Bar dataKey="total" fill="#2563eb" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
