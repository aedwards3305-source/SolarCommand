"use client";

import { useEffect, useRef } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  useMap,
} from "react-leaflet";
import type { LatLngBoundsExpression } from "leaflet";
import "leaflet/dist/leaflet.css";
import type { DiscoveredLeadRow } from "@/lib/types/leadgen";

interface DiscoveryMapProps {
  leads: DiscoveredLeadRow[];
  onSelectLead: (lead: DiscoveredLeadRow) => void;
}

function scoreColor(score: number | null): string {
  if (score == null) return "#9ca3af";
  if (score >= 75) return "#ef4444";
  if (score >= 50) return "#f97316";
  return "#3b82f6";
}

function FitBounds({ leads }: { leads: DiscoveredLeadRow[] }) {
  const map = useMap();
  const prevCount = useRef(0);

  useEffect(() => {
    const pts = leads.filter((l) => l.latitude && l.longitude);
    if (pts.length === 0) return;
    if (pts.length === prevCount.current) return;
    prevCount.current = pts.length;

    const bounds: LatLngBoundsExpression = pts.map(
      (l) => [l.latitude!, l.longitude!] as [number, number]
    );
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
  }, [leads, map]);

  return null;
}

export default function DiscoveryMap({
  leads,
  onSelectLead,
}: DiscoveryMapProps) {
  const defaultCenter: [number, number] = [39.29, -76.61];

  return (
    <div className="relative h-full w-full rounded-xl border border-gray-200 overflow-hidden">
      <MapContainer
        center={defaultCenter}
        zoom={10}
        className="h-full w-full"
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds leads={leads} />

        {leads.map((lead) => {
          if (!lead.latitude || !lead.longitude) return null;
          const color = scoreColor(lead.discovery_score);
          return (
            <CircleMarker
              key={lead.id}
              center={[lead.latitude, lead.longitude]}
              radius={7}
              pathOptions={{
                color: "#fff",
                weight: 2,
                fillColor: color,
                fillOpacity: 0.85,
              }}
              eventHandlers={{ click: () => onSelectLead(lead) }}
            >
              <Popup>
                <div className="text-xs">
                  <p className="font-semibold">{lead.address}</p>
                  <p className="text-gray-500">
                    {lead.city}, {lead.state}
                  </p>
                  <p className="mt-1">
                    Score: {lead.discovery_score ?? "—"}
                    {lead.property_type &&
                      ` · ${lead.property_type.replace(/_/g, " ")}`}
                  </p>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Legend */}
      <div className="absolute top-3 right-3 z-[1000] rounded-lg bg-white/90 px-3 py-2 text-xs shadow-sm backdrop-blur space-y-1">
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
          <span className="text-gray-600">Hot (75+)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-orange-400" />
          <span className="text-gray-600">Warm (50-74)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-blue-400" />
          <span className="text-gray-600">Cool (&lt;50)</span>
        </div>
      </div>

      {leads.length === 0 && (
        <div className="absolute inset-0 z-[1000] flex items-center justify-center bg-white/60">
          <p className="text-gray-400 text-sm">No discovered leads to display</p>
        </div>
      )}
    </div>
  );
}
