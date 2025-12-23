"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface SearchHint {
    name: string;
    regcode: number;
    type: string;
}

export default function HeroSearch() {
    const [query, setQuery] = useState("");
    const [hints, setHints] = useState<SearchHint[]>([]);
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
                        setHints(data);
                        setShowHints(true);
                    })
                    .catch(err => console.error("Search hint error:", err));
            } else {
                setHints([]);
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

    return (
        <div ref={wrapperRef} className="relative w-full max-w-3xl mx-auto z-50">
            <form onSubmit={handleSearch} className="relative shadow-lg rounded-xl">
                <div className="absolute inset-y-0 left-0 flex items-center pl-5 pointer-events-none">
                    <svg className="w-6 h-6 text-purple-500" aria-hidden="true" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>
                </div>
                <input
                    type="search"
                    className="block w-full p-5 pl-14 text-lg text-gray-900 border-0 rounded-xl bg-white focus:ring-4 focus:ring-purple-200 focus:outline-none transition-all placeholder-gray-400"
                    placeholder="Meklēt uzņēmumu, reģ. nr. vai amatpersonu..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onFocus={() => { if (hints.length > 0) setShowHints(true); }}
                />
                <button
                    type="submit"
                    className="absolute right-3 bottom-3 bg-purple-600 text-white hover:bg-purple-700 font-bold rounded-lg text-sm px-6 py-2.5 transition-colors"
                >
                    Meklēt
                </button>
            </form>

            {/* Autocomplete Dropdown */}
            {showHints && hints.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl border border-gray-100 overflow-hidden animate-fade-in-down">
                    <ul>
                        {hints.map((hint) => (
                            <li key={hint.regcode}>
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
                    <div className="bg-gray-50 px-4 py-2 text-center">
                        <button onClick={handleSearch} className="text-xs font-medium text-purple-600 hover:underline">
                            Skatīt visus rezultātus "{query}"
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
