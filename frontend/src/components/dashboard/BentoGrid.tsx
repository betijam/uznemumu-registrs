import React from 'react';
import TopListCard from './TopListCard';
import Link from 'next/link';
import { BuildingOffice2Icon, BanknotesIcon, CircleStackIcon, BoltIcon, FireIcon } from '@heroicons/react/24/outline'; // Need to install heroicons or use existing icons

// Fallback icons if heroicons not installed, but usually we should have them. 
// Assuming heroicons is available or we use simple SVGs.
// Since I don't see package.json contents fully for icons, I'll assume usage of heroicons or replace with SVGs if build fails.
// Let's use simple SVGs to be safe and dependency-free.

const Icons = {
    Building: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>,
    Money: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
    Chart: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" /></svg>,
    Lightning: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>,
    Fire: () => <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" /></svg>
};

interface BentoGridProps {
    tops: {
        turnover: any[];
        profit: any[];
        salaries: any[];
    };
    latest: any[];
    gazeles: any[];
    year?: number;
}

export default function BentoGrid({ tops, latest, gazeles, year = 2024 }: BentoGridProps) {

    const formatCurrency = (val: number) => {
        if (val >= 1e6) return `${(val / 1e6).toFixed(1)} M€`;
        if (val >= 1e3) return `${(val / 1e3).toFixed(1)} K€`;
        return `${val} €`;
    };

    return (
        <div className="w-full max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-8">
                <h2 className="text-2xl font-bold text-gray-900">Biznesa Vides Pārskats ({year})</h2>
                <Link href="/analytics" className="text-sm font-medium text-purple-600 hover:text-purple-700">
                    Skatīt visu analītiku →
                </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

                {/* 1. TOP Turnover */}
                <TopListCard
                    title="TOP Apgrozījums"
                    icon={<Icons.Building />}
                    items={tops.turnover}
                    valueFormatter={(v) => formatCurrency(v)}
                    colorClass="text-blue-600 bg-blue-50"
                    linkTo="/tops/turnover"
                />

                {/* 2. TOP Profit */}
                <TopListCard
                    title="Efektivitāte (Peļņa)"
                    icon={<Icons.Chart />}
                    items={tops.profit}
                    valueFormatter={(v) => formatCurrency(v)}
                    colorClass="text-purple-600 bg-purple-50"
                    linkTo="/tops/profit"
                />

                {/* 3. Latest Registered (Live Feed) */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 flex flex-col h-full relative overflow-hidden">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-orange-50 text-orange-600">
                                <Icons.Lightning />
                            </div>
                            <h3 className="font-semibold text-gray-900">Tikko Reģistrēti</h3>
                        </div>
                        <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-1 rounded animate-pulse">Live</span>
                    </div>

                    <div className="flex-1 space-y-5">
                        {latest.map((company, idx) => (
                            <div key={company.regcode} className="flex justify-between items-start animate-fade-in" style={{ animationDelay: `${idx * 100}ms` }}>
                                <div>
                                    <Link href={`/company/${company.regcode}`} className="font-medium text-gray-900 hover:text-blue-600 block">
                                        {company.name}
                                    </Link>
                                    <p className="text-xs text-gray-400 mt-0.5">{company.regcode}</p>
                                </div>
                                <span className="text-xs font-medium text-purple-600 bg-purple-50 px-2 py-1 rounded-full">
                                    Jauns
                                </span>
                            </div>
                        ))}
                    </div>
                    <div className="mt-6 pt-4 border-t border-gray-50 text-center">
                        <p className="text-xs text-gray-400">Šodien reģistrēti jauni uzņēmumi</p>
                    </div>
                </div>

                {/* 4. Gazeles (Merge into full width or keep in grid?) - Let's make it a large card spanning 2 cols or keep standard.
                   User design showed "Straujākā Izaugsme (Gazeles)" spanning full width or 2 cols.
                   Let's try to make Gazeles span 2 columns if on desktop. 
                */}
                <div className="lg:col-span-2 bg-slate-900 rounded-2xl shadow-sm border border-slate-800 p-8 text-white relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-32 bg-purple-600 rounded-full blur-3xl opacity-20 -mr-16 -mt-16 pointer-events-none"></div>

                    <div className="flex items-center justify-between mb-8 relative z-10">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-white/10 text-pink-400">
                                <Icons.Fire />
                            </div>
                            <h3 className="font-semibold text-lg">Straujākā Izaugsme (Gazeles)</h3>
                        </div>
                        <Link href="/tops/gazelles" className="text-sm font-medium text-slate-300 hover:text-white bg-white/10 px-4 py-2 rounded-lg">
                            Skatīt visus
                        </Link>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
                        {gazeles.slice(0, 3).map((company) => (
                            <div key={company.regcode} className="bg-white/5 rounded-xl p-5 border border-white/10 hover:bg-white/10 transition-colors group cursor-pointer">
                                <div className="text-3xl font-bold text-green-400 mb-2">+{company.growth}%</div>
                                <h4 className="font-bold text-white mb-1 group-hover:text-blue-300 transition-colors line-clamp-1">{company.name}</h4>
                                <p className="text-sm text-slate-400">Apgrozījums sasniedz {formatCurrency(company.turnover)}</p>
                                {company.industry && <p className="text-xs text-slate-500 mt-2 line-clamp-1">{company.industry}</p>}
                            </div>
                        ))}
                    </div>
                </div>

                {/* 5. TOP Salaries */}
                <TopListCard
                    title="Top Algas (Bruto)"
                    icon={<Icons.Money />}
                    items={tops.salaries}
                    valueFormatter={(v) => formatCurrency(v)}
                    colorClass="text-yellow-600 bg-yellow-50"
                    linkTo="/tops/salaries"
                />

            </div>
        </div>
    );
}
