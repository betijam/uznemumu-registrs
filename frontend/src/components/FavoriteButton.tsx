"use client";

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import Cookies from "js-cookie";

interface FavoriteButtonProps {
    entityId: string;
    entityName: string;
    entityType?: string;
}

export default function FavoriteButton({
    entityId,
    entityName,
    entityType = "company"
}: FavoriteButtonProps) {
    const t = useTranslations('Dashboard');
    const [isFavorite, setIsFavorite] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    useEffect(() => {
        const token = Cookies.get('token');
        setIsLoggedIn(!!token);

        if (!!token) {
            checkFavoriteStatus();
        }
    }, [entityId]);

    const checkFavoriteStatus = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/favorites/`, {
                headers: {
                    'Authorization': `Bearer ${Cookies.get('token')}`
                }
            });
            if (res.ok) {
                const favorites = await res.json();
                const found = favorites.some((f: any) => f.entity_id === entityId);
                setIsFavorite(found);
            }
        } catch (error) {
            console.error("Error checking favorite status:", error);
        }
    };

    const toggleFavorite = async () => {
        if (!isLoggedIn) {
            // Optional: Redirect to login or show modal
            window.location.href = `/${window.location.pathname.split('/')[1]}/auth/login`;
            return;
        }

        console.log("FavoriteButton: Toggling favorite. Token exists:", !!Cookies.get('token')); // DEBUG
        setIsLoading(true);
        try {
            if (isFavorite) {
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/favorites/${entityId}?entity_type=${entityType}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${Cookies.get('token')}`
                    }
                });
                if (res.ok) setIsFavorite(false);
            } else {
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/favorites/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${Cookies.get('token')}`
                    },
                    body: JSON.stringify({
                        entity_id: String(entityId),
                        entity_type: entityType,
                        entity_name: entityName
                    })
                });
                if (res.ok) setIsFavorite(true);
            }
        } catch (error) {
            console.error("Error toggling favorite:", error);
            alert("Kļūda saglabājot favorītu. Pārbaudiet konsoli. Error: " + error); // DEBUG
        } finally {
            setIsLoading(false);
        }
    };

    if (!isLoggedIn) return null;

    return (
        <button
            onClick={toggleFavorite}
            disabled={isLoading}
            className={`inline-flex items-center gap-2 px-4 py-2 border rounded-lg text-sm font-medium transition-colors shadow-sm ${isFavorite
                ? 'border-red-200 bg-red-50 text-red-600 hover:bg-red-100'
                : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
                }`}
            title={isFavorite ? t('remove_from_favorites') : t('add_to_favorites')}
        >
            <svg
                className={`w-4 h-4 ${isFavorite ? 'fill-current' : 'fill-none'}`}
                stroke="currentColor"
                viewBox="0 0 24 24"
            >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            <span className="hidden sm:inline">
                {isFavorite ? t('remove_from_favorites') : t('add_to_favorites')}
            </span>
        </button>
    );
}
