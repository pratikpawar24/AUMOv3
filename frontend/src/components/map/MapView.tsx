"use client";
import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import type { POI, RouteResult } from "@/types";

// Fix default marker icons in Next.js
const defaultIcon = typeof window !== "undefined" ? L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
}) : undefined;

const POI_COLORS: Record<string, string> = {
  st_bus_stand: "#E53E3E",
  railway_station: "#3182CE",
  junction: "#DD6B20",
  shop: "#38A169",
  hospital: "#E53E3E",
  education: "#805AD5",
  landmark: "#D69E2E",
  metro: "#319795",
  fuel: "#4A5568",
  government: "#2B6CB0",
};

interface MapViewProps {
  route?: RouteResult | null;
  pois?: POI[];
  onMapClick?: (lat: number, lng: number) => void;
  origin?: { lat: number; lng: number } | null;
  destination?: { lat: number; lng: number } | null;
  className?: string;
}

export default function MapView({ route, pois = [], onMapClick, origin, destination, className = "" }: MapViewProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const layersRef = useRef<L.LayerGroup | null>(null);

  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [18.5204, 73.8567], // Pune, Maharashtra
      zoom: 12,
      zoomControl: true,
    });

    L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
      maxZoom: 19,
    }).addTo(map);

    layersRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;

    if (onMapClick) {
      map.on("click", (e: L.LeafletMouseEvent) => {
        onMapClick(e.latlng.lat, e.latlng.lng);
      });
    }

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Draw route + markers
  useEffect(() => {
    if (!mapRef.current || !layersRef.current) return;
    layersRef.current.clearLayers();

    // Origin marker
    if (origin && defaultIcon) {
      const marker = L.marker([origin.lat, origin.lng], { icon: defaultIcon });
      marker.bindPopup("<b>Origin</b>");
      layersRef.current.addLayer(marker);
    }

    // Destination marker
    if (destination && defaultIcon) {
      const destIcon = L.icon({
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34],
        className: "hue-rotate-[120deg]",
      });
      const marker = L.marker([destination.lat, destination.lng], { icon: destIcon });
      marker.bindPopup("<b>Destination</b>");
      layersRef.current.addLayer(marker);
    }

    // Route polyline
    if (route?.polyline && route.polyline.length > 1) {
      const latlngs = route.polyline.map((p) => [p[0], p[1]] as [number, number]);
      const polyline = L.polyline(latlngs, {
        color: "#059669",
        weight: 5,
        opacity: 0.85,
        smoothFactor: 1,
      });
      layersRef.current.addLayer(polyline);

      // Traffic overlay (color-coded by congestion)
      if (route.trafficOverlay) {
        for (let i = 0; i < route.trafficOverlay.length - 1; i++) {
          const seg = route.trafficOverlay[i];
          const next = route.trafficOverlay[i + 1];
          const color = seg.congestion > 0.7 ? "#EF4444" : seg.congestion > 0.4 ? "#F59E0B" : "#10B981";
          L.polyline(
            [[seg.lat, seg.lng], [next.lat, next.lng]],
            { color, weight: 7, opacity: 0.6 }
          ).addTo(layersRef.current!);
        }
      }

      mapRef.current.fitBounds(polyline.getBounds(), { padding: [50, 50] });
    }

    // POI markers
    pois.forEach((poi) => {
      const color = POI_COLORS[poi.type] || "#6B7280";
      const circle = L.circleMarker([poi.lat, poi.lng], {
        radius: 6,
        fillColor: color,
        color: "#fff",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.85,
      });
      circle.bindPopup(`
        <div style="min-width:150px">
          <b style="color:${color}">${poi.name}</b><br/>
          <small>${poi.type.replace(/_/g, " ").toUpperCase()} • ${poi.city}</small>
        </div>
      `);
      layersRef.current!.addLayer(circle);
    });
  }, [route, pois, origin, destination]);

  return (
    <div ref={mapContainerRef} className={`w-full h-full min-h-[400px] rounded-xl overflow-hidden ${className}`} />
  );
}
