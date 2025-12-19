"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function SearchInput({ className = "" }: { className?: string }) {
    const [query, setQuery] = useState("");
    const router = useRouter();

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim().length > 1) {
            router.push(`/search?q=${encodeURIComponent(query)}`);
        }
    };

    return (
        <form onSubmit={handleSearch} className={`relative max-w-2xl w-full ${className}`}>
            <div className="relative">
                <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
                    <svg className="w-5 h-5 text-gray-400" aria-hidden="true" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>
                </div>
                <input
                    type="search"
                    className="block w-full p-4 pl-12 pr-32 text-sm text-gray-900 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-accent focus:border-accent transition-all"
                    placeholder="Meklēt pēc nosaukuma, reģ. nr. vai amatpersonas..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    required
                />
                <button
                    type="submit"
                    className="absolute right-2.5 bottom-2.5 bg-accent text-white hover:bg-accent/90 focus:ring-4 focus:outline-none focus:ring-accent/30 font-medium rounded-lg text-sm px-5 py-2 transition-colors"
                >
                    Meklēt
                </button>
            </div>
        </form>
    );
}
