'use client';

import { useEffect, useState } from 'react';

interface CompanyMapProps {
    address: string;
}

interface Location {
    lat: number;
    lon: number;
}

export default function CompanyMap({ address }: CompanyMapProps) {
    const [location, setLocation] = useState<Location | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    useEffect(() => {
        const geocode = async () => {
            try {
                // Add 1 second delay to respect Nominatim rate limit
                await new Promise(resolve => setTimeout(resolve, 1000));

                const query = encodeURIComponent(address + ', Latvia');
                const res = await fetch(
                    `https://nominatim.openstreetmap.org/search?q=${query}&format=json&limit=1`,
                    {
                        headers: {
                            'User-Agent': 'CompanyRegistry/1.0'
                        }
                    }
                );

                if (!res.ok) throw new Error('Geocoding failed');

                const data = await res.json();

                if (data[0]) {
                    setLocation({
                        lat: parseFloat(data[0].lat),
                        lon: parseFloat(data[0].lon)
                    });
                } else {
                    setError(true);
                }
            } catch (err) {
                console.error('Geocoding error:', err);
                setError(true);
            } finally {
                setLoading(false);
            }
        };

        if (address) {
            geocode();
        }
    }, [address]);

    if (loading) {
        return (
            <div className="h-48 bg-gray-100 animate-pulse rounded-lg flex items-center justify-center">
                <p className="text-sm text-gray-500">Ielādē karti...</p>
            </div>
        );
    }

    if (error || !location) {
        return null; // Silently fail if geocoding doesn't work
    }

    // Calculate bounding box (±0.01 degrees ~1km)
    const bbox = `${location.lon - 0.01},${location.lat - 0.01},${location.lon + 0.01},${location.lat + 0.01}`;

    return (
        <div className="rounded-lg overflow-hidden shadow-sm border border-gray-200">
            <iframe
                width="100%"
                height="200"
                frameBorder="0"
                loading="lazy"
                src={`https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&marker=${location.lat},${location.lon}&layer=mapnik`}
                style={{ border: 0 }}
                title="Company Location"
            />
            <div className="bg-gray-50 px-3 py-2 text-xs text-gray-600 border-t border-gray-200">
                <a
                    href={`https://www.openstreetmap.org/?mlat=${location.lat}&mlon=${location.lon}#map=15/${location.lat}/${location.lon}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                >
                    Skatīt lielāku karti →
                </a>
            </div>
        </div>
    );
}
