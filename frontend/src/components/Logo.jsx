// RentWise brand logo — teal house mark + "rent wise" wordmark + tagline.
// Recreated as inline SVG so it stays crisp at any size and themeable.

const SIZES = {
  sm: { icon: 26, rent: "text-lg", wise: "text-lg", tag: "text-[7px]" },
  md: { icon: 34, rent: "text-2xl", wise: "text-2xl", tag: "text-[8px]" },
  lg: { icon: 56, rent: "text-4xl", wise: "text-4xl", tag: "text-[11px]" },
  xl: { icon: 84, rent: "text-6xl", wise: "text-6xl", tag: "text-sm" },
};

function HouseMark({ size }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* chimney */}
      <rect x="41" y="12" width="6" height="12" rx="1.5" fill="#0d9488" />
      {/* roof */}
      <path d="M32 9 L57 31 H7 Z" fill="#14b8a0" />
      {/* body */}
      <path d="M13 29 H51 V55 a2 2 0 0 1-2 2 H15 a2 2 0 0 1-2-2 Z" fill="#16bfa6" />
      {/* windows */}
      <g fill="#0d9488">
        <rect x="19" y="35" width="9" height="9" rx="1.5" />
        <rect x="36" y="35" width="9" height="9" rx="1.5" />
      </g>
      <g stroke="#16bfa6" strokeWidth="1.3">
        <line x1="23.5" y1="35" x2="23.5" y2="44" />
        <line x1="19" y1="39.5" x2="28" y2="39.5" />
        <line x1="40.5" y1="35" x2="40.5" y2="44" />
        <line x1="36" y1="39.5" x2="45" y2="39.5" />
      </g>
      {/* door */}
      <path d="M28 57 V48 a4 4 0 0 1 8 0 V57 Z" fill="#0d9488" />
      <circle cx="34" cy="52" r="1" fill="#16bfa6" />
      {/* baseline */}
      <rect x="6" y="57" width="52" height="2.4" rx="1.2" fill="#0d9488" />
    </svg>
  );
}

export default function Logo({ size = "md", showTagline = false, iconOnly = false, light = false }) {
  const s = SIZES[size] ?? SIZES.md;
  const rentColor = light ? "text-white" : "text-gray-900";

  if (iconOnly) return <HouseMark size={s.icon} />;

  return (
    <span className="inline-flex items-center gap-2 select-none">
      <HouseMark size={s.icon} />
      <span className="flex flex-col leading-none">
        <span className={`font-semibold tracking-tight ${s.rent}`}>
          <span className={rentColor}>rent</span>{" "}
          <span className="text-brand-500">wise</span>
        </span>
        {showTagline && (
          <span className={`mt-1 font-medium uppercase tracking-[0.18em] ${s.tag} ${light ? "text-brand-100" : "text-gray-400"}`}>
            Smart rentals, smarter living
          </span>
        )}
      </span>
    </span>
  );
}
