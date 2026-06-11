/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Neutral slate-gray — used for buttons, surfaces and structure
        primary: {
          50:  "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
        },
        // Brand teal from the logo — used only for accents:
        // logo, active states, prices, links, borders, focus rings, shade
        brand: {
          50:  "#ecfdf6",
          100: "#d1faec",
          200: "#a7f3da",
          300: "#6ee7c4",
          400: "#34d3aa",
          500: "#14b8a0",
          600: "#0d9488",
          700: "#0f766e",
        },
      },
      boxShadow: {
        soft: "0 1px 3px 0 rgb(0 0 0 / 0.04), 0 1px 2px -1px rgb(0 0 0 / 0.04)",
        card: "0 4px 16px -4px rgb(15 23 42 / 0.08)",
      },
    },
  },
  plugins: [],
};
