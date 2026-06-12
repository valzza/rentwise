import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import { Link } from "react-router-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Custom teal pin (brand color) as a divIcon — avoids the Leaflet default
// marker-image path issue with bundlers and matches the app theme.
const pin = L.divIcon({
  className: "rentwise-pin",
  html: `<svg width="28" height="28" viewBox="0 0 24 24" fill="#14b8a0" stroke="white" stroke-width="1.5"
           xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 1px 2px rgba(0,0,0,.4))">
           <path d="M12 2C8.1 2 5 5.1 5 9c0 5.2 7 13 7 13s7-7.8 7-13c0-3.9-3.1-7-7-7z"/>
           <circle cx="12" cy="9" r="2.5" fill="white" stroke="none"/>
         </svg>`,
  iconSize: [28, 28],
  iconAnchor: [14, 28],
  popupAnchor: [0, -26],
});

// Property location = its neighborhood coords + a small deterministic jitter
// (by id) so multiple properties in one neighborhood don't stack exactly.
function coords(p) {
  const n = p.neighborhood;
  if (!n || n.latitude == null || n.longitude == null) return null;
  const jLat = (((p.id * 37) % 100) - 50) / 6000;
  const jLng = (((p.id * 53) % 100) - 50) / 6000;
  return [n.latitude + jLat, n.longitude + jLng];
}

const KOSOVO_CENTER = [42.6, 20.9];

export default function PropertyMap({ properties = [], height = "520px", single = false }) {
  const pts = properties.map((p) => ({ p, c: coords(p) })).filter((x) => x.c);
  const center = pts.length ? pts[0].c : KOSOVO_CENTER;
  const zoom = single ? 14 : 8;

  if (pts.length === 0) {
    return (
      <div className="flex items-center justify-center rounded-xl border border-gray-200 bg-white text-sm text-gray-400" style={{ height }}>
        No mapped locations for these properties.
      </div>
    );
  }

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      style={{ height, width: "100%", borderRadius: "0.75rem", zIndex: 0 }}
      scrollWheelZoom={!single}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      {pts.map(({ p, c }) => (
        <Marker key={p.id} position={c} icon={pin}>
          <Popup>
            <div className="text-sm">
              <p className="font-semibold text-gray-900">{p.title}</p>
              <p className="text-brand-600 font-bold">
                ${Number(p.price).toLocaleString()}<span className="font-normal text-gray-500">/mo</span>
              </p>
              <p className="text-xs text-gray-500">{p.neighborhood?.name} · {p.num_rooms} rooms · {p.size_m2} sq ft</p>
              <Link to={`/properties/${p.id}`} className="text-brand-600 underline text-xs">View details →</Link>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
