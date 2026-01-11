"use client";

import { useState, useEffect, useRef } from "react";
import { Link, useRouter } from "@/i18n/routing";
import { useTranslations } from 'next-intl';

interface CompanyHint {
    name: string;
    regcode: number;
    type: string;
}

interface PersonHint {
    name: string;
    person_id: string;
    company_count: number;
    type: string;
}

interface SearchHintsData {
    companies: CompanyHint[];
    persons: PersonHint[];
}

export default function HeroSearch() {
    const t = useTranslations('HeroSearch');
    const [query, setQuery] = useState("");
    const [hints, setHints] = useState<SearchHintsData>({ companies: [], persons: [] });
    const [showHints, setShowHints] = useState(false);
    const router = useRouter();
    const wrapperRef = useRef<HTMLDivElement>(null);

    // Debounce search
    useEffect(() => {
        const timer = setTimeout(() => {
            if (query.length >= 2) {
                fetch(`/api/home/search-hint?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        // Handle both old (array) and new (object) formats gracefully during migration
                        if (Array.isArray(data)) {
                            setHints({ companies: data as any, persons: [] });
                        } else {
                            setHints(data);
                        }
                        setShowHints(true);
                    })
                    .catch(err => console.error("Search hint error:", err));
            } else {
                setHints({ companies: [], persons: [] });
                setShowHints(false);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [query]);

    // Click outside to close
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setShowHints(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [wrapperRef]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim().length > 1) {
            router.push(`/search?q=${encodeURIComponent(query)}`);
            setShowHints(false);
        }
    };

    const hasResults = hints.companies.length > 0 || hints.persons.length > 0;

    return (
        <div ref={wrapperRef} className="relative w-full max-w-3xl mx-auto z-50">
            <form onSubmit={handleSearch} className="relative shadow-2xl rounded-xl">
                <div className="absolute inset-y-0 left-0 flex items-center pl-5 pointer-events-none">
                    <svg className="w-6 h-6 text-purple-500" aria-hidden="true" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>
                </div>
                <input
                    type="search"
                    className="block w-full p-5 pl-14 text-lg text-gray-900 border-0 rounded-xl bg-white focus:ring-4 focus:ring-purple-200 focus:outline-none transition-all placeholder-gray-400"
                    placeholder={t('placeholder')}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onFocus={() => { if (hasResults) setShowHints(true); }}
                />
                <button
                    type="submit"
                    className="absolute right-3 bottom-3 bg-purple-600 text-white hover:bg-purple-700 font-bold rounded-lg text-sm px-6 py-2.5 transition-colors"
                >
                    {t('search_button')}
                </button>
            </form>

            {/* Autocomplete Dropdown */}
            {showHints && hasResults && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl border border-gray-100 overflow-hidden animate-fade-in-down max-h-[80vh] overflow-y-auto z-[100]">

                    {/* Companies Section */}
                    {hints.companies.length > 0 && (
                        <div>
                            <div className="px-4 py-2 bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                {t('companies_header')}
                            </div>
                            <ul>
                                {hints.companies.map((hint) => (
                                    <li key={`comp-${hint.regcode}`}>
                                        <Link
                                            href={`/company/${hint.regcode}`}
                                            className="block px-6 py-3 hover:bg-purple-50 transition-colors border-b border-gray-50 last:border-0"
                                            onClick={() => setShowHints(false)}
                                        >
                                            <div className="flex justify-between items-center">
                                                <span className="font-medium text-gray-800">{hint.name}</span>
                                                <span className="text-xs text-gray-400 font-mono">#{hint.regcode}</span>
                                            </div>
                                            <div className="text-xs text-purple-400 mt-0.5 capitalize">{hint.type}</div>
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Persons Section */}
                    {hints.persons.length > 0 && (
                        <div>
                            <div className="px-4 py-2 bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider border-t border-gray-100">
                                {t('persons_header')}
                            </div>
                            <ul>
                                {hints.persons.map((hint) => (
                                    <li key={`pers-${hint.person_id}`}>
                                        <Link
                                            href={`/person/${hint.person_id}`}
                                            className="block px-6 py-3 hover:bg-purple-50 transition-colors border-b border-gray-50 last:border-0"
                                            onClick={() => setShowHints(false)}
                                        >
                                            <div className="flex justify-between items-center">
                                                <span className="font-medium text-gray-800">{hint.name}</span>
                                                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                                                    {hint.company_count} {t('companies_count_suffix')}
                                                </span>
                                            </div>
                                            <div className="text-xs text-blue-400 mt-0.5 capitalize">{t('person_type')}</div>
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <div className="bg-gray-50 px-4 py-2 text-center sticky bottom-0 border-t border-gray-100">
                        <button onClick={handleSearch} className="text-sm font-medium text-purple-600 hover:text-purple-800">
                            {t('view_all_prefix')} &quot;{query}&quot;
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
