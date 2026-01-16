"use client";

import { useTranslations } from "next-intl";
import { Link, useRouter } from "@/i18n/routing";
import { useState, useEffect } from "react";
import Cookies from "js-cookie";
import { useComparison } from "@/contexts/ComparisonContext";
import CompanySearchBar from "@/components/CompanySearchBar";
import Navbar from "@/components/Navbar";

interface Favorite {
    id: string;
    entity_id: string;
    entity_type: string;
    entity_name: string;
    created_at: string;
    status?: string | null;
    turnover?: number | null;
    profit?: number | null;
    employees?: number | null;
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
    const { selectedCompanies, removeCompany: removeFromComparison } = useComparison();
    const [favorites, setFavorites] = useState<Favorite[]>([]);

    const handleLogout = () => {
        Cookies.remove('token');
        router.push('/');
        router.refresh();
    };
    const [recentViews, setRecentViews] = useState<RecentView[]>([]);
    const [loading, setLoading] = useState(true);
    const [user, setUser] = useState<any>(null);
    const [isSuggestModalOpen, setIsSuggestModalOpen] = useState(false);
    const [suggestion, setSuggestion] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            // Load user info, rich favorites, and recent views
            const [favoritesRes, historyRes] = await Promise.all([
                fetch('/api/favorites/dashboard-list', {
                    headers: {
                        'Authorization': `Bearer ${Cookies.get('token')}`
                    }
                }),
                fetch('/api/history/recent?limit=10', {
                    headers: {
                        'Authorization': `Bearer ${Cookies.get('token')}`
                    }
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

            // Load real user info
            const meRes = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${Cookies.get('token')}`
                }
            });

            if (meRes.ok) {
                const userData = await meRes.json();
                setUser({
                    name: userData.full_name || userData.email.split('@')[0],
                    email: userData.email,
                    initials: (userData.full_name || userData.email)
                        .split(' ')
                        .map((n: any) => n[0])
                        .join('')
                        .toUpperCase()
                        .substring(0, 2)
                });
            } else {
                // If unauthorized, redirect to login
                if (meRes.status === 401) {
                    router.push('/auth/login');
                }
            }

        } catch (error) {
            console.error("Error loading dashboard:", error);
        } finally {
            setLoading(false);
        }
    };

    const removeFavorite = async (entityId: string) => {
        try {
            const res = await fetch(`/api/favorites/${entityId}?entity_type=company`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${Cookies.get('token')}`
                }
            });

            if (res.ok) {
                setFavorites(favorites.filter(f => f.entity_id !== entityId));
            }
        } catch (error) {
            console.error("Error removing favorite:", error);
        }
    };

    const addFavoriteFromSearch = async (company: any) => {
        try {
            const res = await fetch('/api/favorites', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${Cookies.get('token')}`
                },
                body: JSON.stringify({
                    entity_id: String(company.regcode),
                    entity_type: 'company',
                    entity_name: company.name
                })
            });

            if (res.ok) {
                // Refresh favorites
                const favRes = await fetch('/api/favorites', {
                    headers: {
                        'Authorization': `Bearer ${Cookies.get('token')}`
                    }
                });
                if (favRes.ok) {
                    const favData = await favRes.json();
                    setFavorites(favData);
                }
            }
        } catch (error) {
            console.error("Error adding favorite:", error);
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
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

    const handleSuggest = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);

        try {
            const res = await fetch('/api/waitlist/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${Cookies.get('token')}`
                },
                body: JSON.stringify({
                    feedback_text: suggestion,
                    email: user?.email,
                    source: 'dashboard'
                })
            });

            if (res.ok) {
                setIsSuggestModalOpen(false);
                setSuggestion("");
                // Show success message (you can replace alert with a toast notification)
                alert(t('suggestion_success'));
            } else {
                alert("Kļūda nosūtot ieteikumu. Mēģiniet vēlāk.");
            }
        } catch (error) {
            console.error("Error submitting feedback:", error);
            alert("Kļūda nosūtot ieteikumu.");
        } finally {
            setIsSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50">
                <Navbar />
                <div className="flex items-center justify-center py-20">
                    <div className="text-gray-500">Ielādē...</div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Navbar />
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


                            <button
                                onClick={handleLogout}
                                className="w-full mt-2 py-2 text-red-600 text-sm font-medium hover:underline text-center"
                            >
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
                                    {t('roadmap_item_1')}
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 bg-yellow-400 rounded-full"></span>
                                    {t('roadmap_item_2')}
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 bg-purple-400 rounded-full"></span>
                                    {t('roadmap_item_3')}
                                </li>
                            </ul>
                            <button
                                onClick={() => setIsSuggestModalOpen(true)}
                                className="w-full py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-medium transition-colors border border-white/10"
                            >
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
                                <div className="bg-white border border-gray-200 rounded-xl p-8 text-center flex flex-col items-center">
                                    <p className="text-gray-500 mb-6">{t('favorites_empty')}</p>
                                    <div className="w-full max-w-md">
                                        <CompanySearchBar onSelectCompany={addFavoriteFromSearch} />
                                    </div>
                                </div>
                            ) : (
                                <div className="bg-white border border-gray-200 rounded-xl divide-y divide-gray-100 overflow-hidden shadow-sm">
                                    {favorites.map((fav) => (
                                        <div key={fav.id} className="p-4 hover:bg-gray-50 transition-colors flex items-center justify-between group">
                                            <div className="flex items-center gap-4 flex-1">
                                                <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-xs font-bold ${fav.entity_type === 'person'
                                                        ? 'bg-purple-100 text-purple-600'
                                                        : 'bg-blue-50 text-blue-600'
                                                    }`}>
                                                    {fav.entity_type === 'person' ? (
                                                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                                        </svg>
                                                    ) : (
                                                        fav.entity_name.substring(0, 2).toUpperCase()
                                                    )}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2">
                                                        <Link href={`/${fav.entity_type === 'person' ? 'person' : 'company'}/${fav.entity_id}`} className="font-semibold text-slate-900 hover:text-indigo-600 truncate max-w-[200px] sm:max-w-xs block">
                                                            {fav.entity_name}
                                                        </Link>
                                                        {['active', 'aktīvs', 'reģistrēts', 'a'].includes((fav.status || '').toLowerCase()) && (
                                                            <span className="px-1.5 py-0.5 bg-green-100 text-green-700 text-[10px] font-bold uppercase rounded tracking-wide">Aktīvs</span>
                                                        )}
                                                    </div>

                                                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500 mt-1">
                                                        <span>{fav.entity_type === 'company' ? 'Reģ. nr.' : 'Personas kods'}: {fav.entity_id}</span>

                                                        {fav.turnover !== undefined && fav.turnover !== null && (
                                                            <span className="flex items-center gap-1 text-slate-700 font-medium">
                                                                <svg className="w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                                </svg>
                                                                {(fav.turnover / 1000000).toFixed(2)}M €
                                                            </span>
                                                        )}

                                                        {fav.profit !== undefined && fav.profit !== null && (
                                                            <span className={`flex items-center gap-1 font-medium ${fav.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                                {fav.profit >= 0 ? '+' : ''}{(fav.profit / 1000).toFixed(0)}K €
                                                            </span>
                                                        )}

                                                        {fav.employees !== undefined && fav.employees !== null && (
                                                            <span className="flex items-center gap-1 text-slate-600">
                                                                <svg className="w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                                                                </svg>
                                                                {fav.employees} darb.
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => removeFavorite(fav.entity_id)}
                                                className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors ml-2"
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





                    </div>

                </div>
            </div>

            {/* Suggestion Modal */}
            {isSuggestModalOpen && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
                    <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setIsSuggestModalOpen(false)}></div>
                    <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg relative z-10 overflow-hidden">
                        <div className="p-6 border-b border-gray-100 flex justify-between items-center">
                            <h3 className="text-xl font-bold text-slate-900">{t('suggest_modal_title')}</h3>
                            <button onClick={() => setIsSuggestModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                        <form onSubmit={handleSuggest} className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">{t('suggest_label')}</label>
                                <textarea
                                    required
                                    value={suggestion}
                                    onChange={(e) => setSuggestion(e.target.value)}
                                    className="w-full h-40 px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none resize-none"
                                    placeholder={t('suggest_placeholder')}
                                ></textarea>
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setIsSuggestModalOpen(false)}
                                    className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                                >
                                    {t('cancel')}
                                </button>
                                <button
                                    type="submit"
                                    disabled={isSubmitting || !suggestion.trim()}
                                    className="flex-1 px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isSubmitting ? t('sending') : t('send_suggestion')}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
