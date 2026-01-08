"use client";

import { useEffect, useState, useMemo } from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import {
    MetricType,
    RegionProperties,
    getColor,
    getColorScale,
    formatValue,
    calculateCentroid,
    LATVIA_CENTER,
    LATVIA_BOUNDS,
} from "@/lib/mapUtils";
import LayerControl from "./LayerControl";
import MapLegend from "./MapLegend";

// Dynamic import to avoid SSR issues with Leaflet
const MapContainer = dynamic(
    () => import("react-leaflet").then((mod) => mod.MapContainer),
    { ssr: false }
);
const TileLayer = dynamic(
    () => import("react-leaflet").then((mod) => mod.TileLayer),
    { ssr: false }
);
const GeoJSON = dynamic(
    () => import("react-leaflet").then((mod) => mod.GeoJSON),
    { ssr: false }
);
const CircleMarker = dynamic(
    () => import("react-leaflet").then((mod) => mod.CircleMarker),
    { ssr: false }
);
const Popup = dynamic(
    () => import("react-leaflet").then((mod) => mod.Popup),
    { ssr: false }
);
const Tooltip = dynamic(
    () => import("react-leaflet").then((mod) => mod.Tooltip),
    { ssr: false }
);

interface RegionsMapProps {
    onRegionClick?: (regionName: string, locationType: string) => void;
}

export default function RegionsMap({ onRegionClick }: RegionsMapProps) {
    const router = useRouter();
    const [geoData, setGeoData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [selectedMetric, setSelectedMetric] = useState<MetricType>("total_revenue");
    const [showBubbles, setShowBubbles] = useState(false);
    const [showTopPerformers, setShowTopPerformers] = useState(false);
    const [showCities, setShowCities] = useState(true); // Default ON to show cities
    const [citiesData, setCitiesData] = useState<any[]>([]);
    const [hoveredRegion, setHoveredRegion] = useState<string | null>(null);

    // Load GeoJSON data
    useEffect(() => {
        fetch("/api/map/geojson")
            .then((res) => res.json())
            .then((data) => {
                setGeoData(data);
                setLoading(false);
            })
            .catch((err) => {
                console.error("Failed to load GeoJSON:", err);
                setLoading(false);
            });

        // Load cities data
        fetch("/api/map/cities")
            .then((res) => res.json())
            .then((data) => setCitiesData(data))
            .catch((err) => console.error("Failed to load cities:", err));
    }, []);

    // Get color scale thresholds for legend
    const colorScale = useMemo(() => {
        return getColorScale(selectedMetric);
    }, [selectedMetric]);

    // Get top performers for overlay
    const topPerformers = useMemo(() => {
        if (!geoData) return [];
        return [...geoData.features]
            .sort((a: any, b: any) => (b.properties[selectedMetric] || 0) - (a.properties[selectedMetric] || 0))
            .slice(0, 10)
            .map((feature: any) => {
                const coords = feature.geometry.type === "MultiPolygon"
                    ? feature.geometry.coordinates[0]
                    : feature.geometry.coordinates;
                return {
                    name: feature.properties.name,
                    center: calculateCentroid(coords),
                    value: feature.properties[selectedMetric] || 0,
                };
            });
    }, [geoData, selectedMetric]);

    // Calculate centroids for bubble overlay
    const regionCentroids = useMemo(() => {
        if (!geoData) return [];
        return geoData.features.map((feature: any) => {
            const coords = feature.geometry.type === "MultiPolygon"
                ? feature.geometry.coordinates[0]
                : feature.geometry.coordinates;
            return {
                name: feature.properties.name,
                center: calculateCentroid(coords),
                employees: feature.properties.total_employees || 0,
                value: feature.properties[selectedMetric] || 0,
            };
        });
    }, [geoData, selectedMetric]);

    // Style function for GeoJSON features
    const getFeatureStyle = (feature: any) => {
        const value = feature.properties[selectedMetric] || 0;
        const isHovered = hoveredRegion === feature.properties.name;

        return {
            fillColor: getColor(value, selectedMetric),
            weight: isHovered ? 3 : 1,
            opacity: 1,
            color: isHovered ? "#1e40af" : "#666",
            fillOpacity: isHovered ? 0.9 : 0.7,
        };
    };

    // Handle region click
    const handleRegionClick = (feature: any) => {
        const props = feature.properties as RegionProperties;
        const locationType = props.location_type === "city" ? "city" : "municipality";
        const name = props.db_name || props.name;

        if (onRegionClick) {
            onRegionClick(name, locationType);
        } else {
            router.push(`/regions/${locationType}/${encodeURIComponent(name)}`);
        }
    };

    // Event handlers for each feature
    const onEachFeature = (feature: any, layer: any) => {
        const props = feature.properties as RegionProperties;

        layer.on({
            mouseover: () => setHoveredRegion(props.name),
            mouseout: () => setHoveredRegion(null),
            click: () => handleRegionClick(feature),
        });

        // Add tooltip
        layer.bindTooltip(
            `<div class="font-semibold">${props.name}</div>
       <div class="text-sm">
         ${formatValue(props[selectedMetric] || 0, selectedMetric)}
       </div>`,
            { sticky: true, className: "custom-tooltip" }
        );
    };

    if (loading) {
        return (
            <div className="w-full h-[600px] bg-gray-100 rounded-xl flex items-center justify-center">
                <div className="text-gray-500">Ielādē karti...</div>
            </div>
        );
    }

    if (!geoData) {
        return (
            <div className="w-full h-[600px] bg-red-50 rounded-xl flex items-center justify-center">
                <div className="text-red-500">Neizdevās ielādēt kartes datus</div>
            </div>
        );
    }

    return (
        <div className="relative w-full h-[600px] rounded-xl overflow-hidden shadow-lg">
            <MapContainer
                center={LATVIA_CENTER}
                zoom={7}
                style={{ height: "100%", width: "100%" }}
                maxBounds={LATVIA_BOUNDS}
                minZoom={6}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                />

                {/* Choropleth Layer */}
                <GeoJSON
                    key={`${selectedMetric}-${hoveredRegion}`}
                    data={geoData}
                    style={getFeatureStyle}
                    onEachFeature={onEachFeature}
                />

                {/* Density Bubbles Overlay */}
                {showBubbles &&
                    regionCentroids.map((region: any) => (
                        <CircleMarker
                            key={region.name}
                            center={region.center}
                            radius={Math.max(5, Math.sqrt(region.employees) / 10)}
                            pathOptions={{
                                color: "#1e40af",
                                fillColor: "#3b82f6",
                                fillOpacity: 0.6,
                                weight: 1,
                            }}
                        >
                            <Tooltip>
                                <div className="font-semibold">{region.name}</div>
                                <div className="text-sm">{region.employees.toLocaleString()} darbinieki</div>
                            </Tooltip>
                        </CircleMarker>
                    ))}

                {/* Top Performers Overlay */}
                {showTopPerformers &&
                    topPerformers.map((region: any, index: number) => (
                        <CircleMarker
                            key={`top-${region.name}`}
                            center={region.center}
                            radius={12 - index}
                            pathOptions={{
                                color: "#dc2626",
                                fillColor: "#fbbf24",
                                fillOpacity: 0.9,
                                weight: 2,
                            }}
                        >
                            <Tooltip>
                                <div className="font-semibold">#{index + 1} {region.name}</div>
                                <div className="text-sm">{formatValue(region.value, selectedMetric)}</div>
                            </Tooltip>
                        </CircleMarker>
                    ))}

                {/* Cities Overlay */}
                {showCities &&
                    citiesData.map((city: any) => (
                        <CircleMarker
                            key={`city-${city.name}`}
                            center={[city.lat, city.lng]}
                            radius={Math.max(4, Math.log10(city.company_count + 1) * 3)}
                            pathOptions={{
                                color: "#1e3a5f",
                                fillColor: getColor(city[selectedMetric.replace('total_', '')] || city[selectedMetric] || 0, selectedMetric),
                                fillOpacity: 0.85,
                                weight: 2,
                            }}
                        >
                            <Tooltip>
                                <div className="font-semibold">{city.name}</div>
                                <div className="text-sm">{city.company_count.toLocaleString()} uzņēmumi</div>
                                <div className="text-sm">{formatValue(city[selectedMetric] || 0, selectedMetric)}</div>
                            </Tooltip>
                        </CircleMarker>
                    ))}
            </MapContainer>

            {/* Layer Control Panel */}
            <LayerControl
                selectedMetric={selectedMetric}
                onMetricChange={setSelectedMetric}
                showBubbles={showBubbles}
                onBubblesChange={setShowBubbles}
                showTopPerformers={showTopPerformers}
                onTopPerformersChange={setShowTopPerformers}
                showCities={showCities}
                onShowCitiesChange={setShowCities}
            />

            {/* Legend */}
            <MapLegend metric={selectedMetric} />

            {/* CSS for custom tooltip */}
            <style jsx global>{`
        .custom-tooltip {
          background: white;
          border: none;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          padding: 8px 12px;
        }
        .leaflet-tooltip-left:before,
        .leaflet-tooltip-right:before {
          border: none;
        }
      `}</style>
        </div>
    );
}
