"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import debounce from "lodash.debounce";
import { formatCompanyName } from '@/utils/formatCompanyName';

interface Company {
    regcode: number;
    name: string;
    name_in_quotes?: string;
    type?: string;
    status?: string;
}

export default function CompanySearchBar() {
    const router = useRouter();
    const [searchQuery, setSearchQuery] = useState("");
    const [suggestions, setSuggestions] = useState<Company[]>([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [isSearching, setIsSearching] = useState(false);

    // Debounced search
    const searchCompanies = useCallback(
        debounce(async (query: string) => {
            if (query.length < 2) {
                setSuggestions([]);
                return;
            }
            setIsSearching(true);
            try {
                const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const data = await res.json();
                setSuggestions(data.slice(0, 8));
                setShowDropdown(true);
            } catch (e) {
                console.error("Search failed:", e);
            } finally {
                setIsSearching(false);
            }
        }, 300),
        []
    );

    useEffect(() => {
        searchCompanies(searchQuery);
    }, [searchQuery, searchCompanies]);

    const handleSelectCompany = (company: Company) => {
        setSearchQuery("");
        setShowDropdown(false);
        setSuggestions([]);
        router.push(`/company/${company.regcode}`);
    };

    return (
        <div className="relative">
            <div className="flex items-center gap-2">
                <div className="relative flex-1">
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Meklēt citu uzņēmumu..."
                        className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary text-sm"
                        onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
                        onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                    />
                    <svg
                        className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        />
                    </svg>
                    {isSearching && (
                        <div className="absolute right-3 top-1/2 -translate-y-1/2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                        </div>
                    )}
                </div>
            </div>

            {/* Dropdown */}
            {showDropdown && suggestions.length > 0 && (
                <div className="absolute w-full mt-1 bg-white rounded-lg shadow-xl z-[9999] overflow-hidden border border-gray-200 max-h-80 overflow-y-auto">
                    {suggestions.map((company) => (
                        <button
                            key={company.regcode}
                            onClick={() => handleSelectCompany(company)}
                            className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center justify-between border-b last:border-0 transition-colors"
                        >
                            <div>
                                <span className="font-medium text-gray-900">{formatCompanyName(company)}</span>
                                <span className="text-sm text-gray-500 ml-2">({company.regcode})</span>
                            </div>
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
