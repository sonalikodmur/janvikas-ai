import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export default function MapView({ hotspots, onSelect }) {
  const el = useRef(null), map = useRef(null), layer = useRef(null);
  useEffect(() => {
    map.current = L.map(el.current).setView([19.4, 76.5], 6);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: "© OpenStreetMap contributors" }).addTo(map.current);
    layer.current = L.layerGroup().addTo(map.current);
    return () => map.current.remove();
  }, []);
  useEffect(() => {
    layer.current.clearLayers();
    hotspots.forEach((h, i) => {
      // offset markers in the same district so they don't overlap exactly
      const off = (hotspots.filter((x, j) => j < i && x.district === h.district).length) * 0.12;
      L.circleMarker([h.lat + off, h.lng + off], { radius: 6 + Math.sqrt(h.request_count) * 1.6,
        color: "#0369a1", fillColor: h.score > 60 ? "#dc2626" : "#38bdf8", fillOpacity: 0.7 })
        .bindTooltip(`${h.district} · ${h.category}: ${h.request_count}`).on("click", () => onSelect(h)).addTo(layer.current);
    });
  }, [hotspots]);
  return <div ref={el} className="h-[380px] w-full rounded-lg z-0" role="application" aria-label="Hotspot map" />;
}
