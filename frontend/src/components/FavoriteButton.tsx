"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface FavoriteButtonProps {
    entityId: string;
    entityName: string;
    entityType?: "company" | "person";
    className?: string;
}

export default function FavoriteButton({
    entityId,
    entityName,
    entityType = "company",
    className = ""
}: FavoriteButtonProps) {
    const [isFavorite, setIsFavorite] = useState(false);
    const [loading, setLoading] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const router = useRouter();

    useEffect(() => {
        checkFavoriteStatus();
    }, [entityId]);

    const checkFavoriteStatus = async () => {
        try {
            const res = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/favorites/check/${entityId}?entity_type=${entityType}`,
                { credentials: 'include' }
            );

            if (res.ok) {
                const data = await res.json();
                setIsFavorite(data.is_favorite);
                setIsAuthenticated(true);
            } else if (res.status === 401) {
                setIsAuthenticated(false);
            }
        } catch (error) {
            console.error("Error checking favorite status:", error);
        }
    };

    const toggleFavorite = async (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();

        if (!isAuthenticated) {
            // Redirect to login
            router.push('/auth/login');
            return;
        }

        // Optimistic UI update
        const previousState = isFavorite;
        setIsFavorite(!isFavorite);
        setLoading(true);

        try {
            if (isFavorite) {
                // Remove from favorites
                const res = await fetch(
                    `${process.env.NEXT_PUBLIC_API_URL}/favorites/${entityId}?entity_type=${entityType}`,
                    {
                        method: 'DELETE',
                        credentials: 'include'
                    }
                );

                if (!res.ok) {
                    throw new Error('Failed to remove favorite');
                }
            } else {
                // Add to favorites
                const res = await fetch(
                    `${process.env.NEXT_PUBLIC_API_URL}/favorites/`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'include',
                        body: JSON.stringify({
                            entity_id: entityId,
                            entity_type: entityType,
                            entity_name: entityName
                        })
                    }
                );

                if (!res.ok) {
                    throw new Error('Failed to add favorite');
                }
            }
        } catch (error) {
            console.error("Error toggling favorite:", error);
            // Revert optimistic update on error
            setIsFavorite(previousState);
        } finally {
            setLoading(false);
        }
    };

    return (
        <button
            onClick={toggleFavorite}
            disabled={loading}
            className={`group relative inline-flex items-center justify-center p-2 rounded-lg transition-all ${isFavorite
                    ? 'text-red-500 hover:bg-red-50'
                    : 'text-gray-400 hover:text-red-500 hover:bg-red-50'
                } ${loading ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
            title={isFavorite ? "Noņemt no favorītiem" : "Pievienot favorītiem"}
        >
            <svg
                className="w-6 h-6 transition-transform group-hover:scale-110"
                fill={isFavorite ? "currentColor" : "none"}
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
            >
                <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                />
            </svg>

            {/* Tooltip */}
            <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 text-xs font-medium text-white bg-gray-900 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                {isFavorite ? "Noņemt no favorītiem" : "Pievienot favorītiem"}
            </span>
        </button>
    );
}
