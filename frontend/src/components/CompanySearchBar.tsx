"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "@/i18n/routing";
import debounce from "lodash.debounce";
import { formatCompanyName } from '@/utils/formatCompanyName';

interface Company {
    regcode: number;
    name: string;
    name_in_quotes?: string;
    type?: string;
    status?: string;
}

interface Person {
    person_id: string;
    name: string;
}

interface SearchResults {
    companies: Company[];
    persons: Person[];
}

export default function CompanySearchBar() {
    const router = useRouter();
    const [searchQuery, setSearchQuery] = useState("");
    const [results, setResults] = useState<SearchResults>({ companies: [], persons: [] });
    const [showDropdown, setShowDropdown] = useState(false);
    const [isSearching, setIsSearching] = useState(false);

    // Debounced search
    const searchAll = useCallback(
        debounce(async (query: string) => {
            if (query.length < 2) {
                setResults({ companies: [], persons: [] });
                return;
            }
            setIsSearching(true);
            try {
                const res = await fetch(`/api/home/search-hint?q=${encodeURIComponent(query)}`);
                const data = await res.json();

                // Handle both old (array) and new (object) formats gracefully
                if (Array.isArray(data)) {
                    setResults({ companies: data.slice(0, 5), persons: [] });
                } else {
                    setResults({
                        companies: data.companies?.slice(0, 5) || [],
                        persons: data.persons?.slice(0, 5) || []
                    });
                }
                setShowDropdown(true);
            } catch (e) {
                console.error("Search failed:", e);
            } finally {
                setIsSearching(false);
            }
        }, 150),
        []
    );

    useEffect(() => {
        searchAll(searchQuery);
    }, [searchQuery, searchAll]);

    const handleSelectCompany = (company: Company) => {
        setSearchQuery("");
        setShowDropdown(false);
        setResults({ companies: [], persons: [] });
        router.push(`/company/${company.regcode}`);
    };

    const handleSelectPerson = (person: Person) => {
        setSearchQuery("");
        setShowDropdown(false);
        setResults({ companies: [], persons: [] });
        router.push(`/person/${person.person_id}`);
    };

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (searchQuery.trim().length > 1) {
            router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
            setShowDropdown(false);
        }
    };

    const hasResults = results.companies.length > 0 || results.persons.length > 0;

    return (
        <div className="relative">
            <form onSubmit={handleSearch} className="flex items-center gap-2">
                <div className="relative flex-1">
                    <input
                        type="search"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Meklēt uzņēmumu vai personu..."
                        className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary text-sm"
                        onFocus={() => hasResults && setShowDropdown(true)}
                        onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
                    />
                    <button type="submit" className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-primary transition-colors">
                        <svg
                            className="w-4 h-4"
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
                    </button>
                    {isSearching && (
                        <div className="absolute right-3 top-1/2 -translate-y-1/2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                        </div>
                    )}
                </div>
            </form>

            {/* Dropdown */}
            {showDropdown && hasResults && (
                <div className="absolute w-full mt-1 bg-white rounded-lg shadow-xl z-[9999] overflow-hidden border border-gray-200 max-h-80 overflow-y-auto">
                    {/* Companies Section */}
                    {results.companies.length > 0 && (
                        <div>
                            <div className="px-3 py-2 bg-gray-50 text-xs font-semibold text-gray-500 uppercase">
                                Uzņēmumi
                            </div>
                            {results.companies.map((company) => (
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

                    {/* Persons Section */}
                    {results.persons.length > 0 && (
                        <div>
                            <div className="px-3 py-2 bg-gray-50 text-xs font-semibold text-gray-500 uppercase border-t">
                                Personas
                            </div>
                            {results.persons.map((person) => (
                                <button
                                    key={person.person_id}
                                    onClick={() => handleSelectPerson(person)}
                                    className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center justify-between border-b last:border-0 transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        <span className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-sm">
                                            {person.name.split(' ').map(n => n[0]).join('').substring(0, 2)}
                                        </span>
                                        <span className="font-medium text-gray-900">{person.name}</span>
                                    </div>
                                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                </button>
                            ))}
                        </div>
                    )}

                    {/* View All Button */}
                    <div className="bg-gray-50 px-4 py-2 text-center sticky bottom-0 border-t border-gray-100">
                        <button
                            onMouseDown={(e) => {
                                e.preventDefault(); // Prevent blur
                                handleSearch(e as unknown as React.FormEvent);
                            }}
                            className="text-sm font-medium text-primary hover:text-primary/80"
                        >
                            Skatīt visus rezultātus ({searchQuery}) &rarr;
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
