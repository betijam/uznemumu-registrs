"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/routing";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface Favorite {
    id: string;
    entity_id: string;
    entity_type: string;
    entity_name: string;
    created_at: string;
}

interface RecentView {
    entity_id: string;
    entity_type: string;
    entity_name: string;
    viewed_at: string;
}

export default function DashboardPage() {
    const t = useTranslations('Dashboard');
    const router = useRouter();
    const [favorites, setFavorites] = useState<Favorite[]>([]);
    const [recentViews, setRecentViews] = useState<RecentView[]>([]);
    const [loading, setLoading] = useState(true);
    const [user, setUser] = useState<any>(null);

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            // Load user info, favorites, and recent views
            const [favoritesRes, historyRes] = await Promise.all([
                fetch(`${process.env.NEXT_PUBLIC_API_URL}/favorites/`, {
                    credentials: 'include'
                }),
                fetch(`${process.env.NEXT_PUBLIC_API_URL}/history/recent?limit=10`, {
                    credentials: 'include'
                })
            ]);

            if (favoritesRes.ok) {
                const favData = await favoritesRes.json();
                setFavorites(favData);
            }

            if (historyRes.ok) {
                const histData = await historyRes.json();
                setRecentViews(histData);
            }

            // TODO: Load user info from auth context
            setUser({
                name: "Jānis Bērziņš",
                email: "janis@uznemums.lv",
                initials: "JB"
            });

        } catch (error) {
            console.error("Error loading dashboard:", error);
        } finally {
            setLoading(false);
        }
    };

    const removeFavorite = async (entityId: string) => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/favorites/${entityId}?entity_type=company`, {
                method: 'DELETE',
                credentials: 'include'
            });

            if (res.ok) {
                setFavorites(favorites.filter(f => f.entity_id !== entityId));
            }
        } catch (error) {
            console.error("Error removing favorite:", error);
        }
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 60) return `Pirms ${diffMins} min`;
        if (diffHours < 24) return `Pirms ${diffHours}h`;
        if (diffDays === 0) return "Šodien";
        if (diffDays === 1) return "Vakar";
        return date.toLocaleDateString('lv-LV');
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-gray-500">Ielādē...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">

                {/* Header */}
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-slate-900">{t('title')}</h1>
                        <p className="text-slate-500 text-sm">{t('subtitle')}</p>
                    </div>
                    <Link href="/" className="text-sm font-medium text-indigo-600 hover:text-indigo-800">
                        ← {t('back_to_search')}
                    </Link>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                    {/* Left Sidebar */}
                    <div className="space-y-6">

                        {/* User Profile Card */}
                        <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm">
                            <div className="flex items-center gap-4 mb-6">
                                <div className="w-16 h-16 rounded-full bg-slate-900 text-white flex items-center justify-center text-2xl font-bold">
                                    {user?.initials || "U"}
                                </div>
                                <div>
                                    <h2 className="font-bold text-lg">{user?.name || "Lietotājs"}</h2>
                                    <p className="text-slate-500 text-sm">{user?.email || ""}</p>
                                </div>
                            </div>

                            <div className="border-t border-gray-100 pt-4 mb-4">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-sm text-slate-600">{t('plan')}</span>
                                    <span className="px-2 py-0.5 rounded text-xs font-bold bg-green-100 text-green-700">Basic (Bezmaksas)</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-slate-600">{t('status')}</span>
                                    <span className="px-2 py-0.5 rounded text-xs font-bold bg-indigo-100 text-indigo-700">{t('beta_tester')} 🚀</span>
                                </div>
                            </div>

                            <button className="w-full py-2 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 text-slate-700">
                                {t('edit_profile')}
                            </button>
                            <button className="w-full mt-2 py-2 text-red-600 text-sm font-medium hover:underline">
                                {t('logout')}
                            </button>
                        </div>

                        {/* Roadmap Teaser Card */}
                        <div className="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-2xl p-6 text-white relative overflow-hidden">
                            <div className="absolute top-0 right-0 -mr-4 -mt-4 w-24 h-24 bg-white/10 rounded-full blur-xl"></div>

                            <h3 className="font-bold text-lg mb-2">{t('whats_next')}</h3>
                            <p className="text-indigo-200 text-sm mb-4 leading-relaxed">
                                {t('whats_next_desc')}
                            </p>
                            <ul className="space-y-2 text-sm text-indigo-100 mb-6">
                                <li className="flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
                                    Excel datu eksports
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 bg-yellow-400 rounded-full"></span>
                                    Monitorings (Alerts)
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 bg-purple-400 rounded-full"></span>
                                    10 gadu vēsture
                                </li>
                            </ul>
                            <button className="w-full py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-medium transition-colors border border-white/10">
                                {t('suggest_feature')}
                            </button>
                        </div>

                    </div>

                    {/* Main Content */}
                    <div className="lg:col-span-2 space-y-8">

                        {/* Favorites Section */}
                        <div>
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                                    <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd"></path>
                                    </svg>
                                    {t('favorites_title')}
                                </h3>
                                <span className="text-xs font-medium bg-gray-200 text-gray-600 px-2 py-1 rounded-full">{favorites.length}</span>
                            </div>

                            {favorites.length === 0 ? (
                                <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
                                    <p className="text-gray-500 mb-4">{t('favorites_empty')}</p>
                                    <Link href="/" className="text-indigo-600 hover:text-indigo-800 font-medium">
                                        {t('back_to_search')} →
                                    </Link>
                                </div>
                            ) : (
                                <div className="bg-white border border-gray-200 rounded-xl divide-y divide-gray-100 overflow-hidden shadow-sm">
                                    {favorites.map((fav) => (
                                        <div key={fav.id} className="p-4 hover:bg-gray-50 transition-colors flex items-center justify-between group">
                                            <div className="flex items-center gap-4 flex-1">
                                                <div className="w-10 h-10 rounded bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-500">
                                                    {fav.entity_name.substring(0, 2).toUpperCase()}
                                                </div>
                                                <div className="flex-1">
                                                    <Link href={`/company/${fav.entity_id}`} className="font-semibold text-slate-900 hover:text-indigo-600 block">
                                                        {fav.entity_name}
                                                    </Link>
                                                    <div className="flex items-center gap-2 text-xs text-gray-500 mt-0.5">
                                                        <span>Reģ. nr: {fav.entity_id}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => removeFavorite(fav.entity_id)}
                                                className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                                title="Noņemt no favorītiem"
                                            >
                                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Recently Viewed */}
                        <div>
                            <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                                <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                {t('recent_title')}
                            </h3>

                            {recentViews.length === 0 ? (
                                <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
                                    <p className="text-gray-500">{t('recent_empty')}</p>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    {recentViews.slice(0, 6).map((view) => (
                                        <Link
                                            key={`${view.entity_id}-${view.viewed_at}`}
                                            href={`/company/${view.entity_id}`}
                                            className="block p-4 bg-white border border-gray-200 rounded-xl hover:shadow-md hover:border-indigo-300 transition-all"
                                        >
                                            <span className="text-xs text-gray-400 mb-1 block">{formatDate(view.viewed_at)}</span>
                                            <span className="font-bold text-slate-900 block truncate">{view.entity_name}</span>
                                            <span className="text-xs text-indigo-600 mt-2 block font-medium">Skatīt profilu →</span>
                                        </Link>
                                    ))}
                                </div>
                            )}
                        </div>

                    </div>

                </div>
            </div>
        </div>
    );
}
