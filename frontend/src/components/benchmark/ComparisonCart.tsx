"use client";

import { useComparison } from '@/contexts/ComparisonContext';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function ComparisonCart() {
    const { selectedCompanies, removeCompany, clearAll } = useComparison();
    const router = useRouter();

    if (selectedCompanies.length === 0) {
        return null; // Don't show if empty
    }

    const handleOpenComparison = () => {
        const regcodes = selectedCompanies.map(c => c.regcode).join(',');
        const currentYear = new Date().getFullYear();
        router.push(`/benchmark?companies=${regcodes}&year=${currentYear}`);
    };

    return (
        <div className="fixed top-20 right-4 z-50 w-80 bg-white rounded-lg shadow-xl border border-gray-200">
            {/* Header */}
            <div className="bg-gradient-to-r from-primary to-primary-dark text-white px-4 py-3 rounded-t-lg">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                        <h3 className="font-semibold">Salīdzināšanas grozs</h3>
                    </div>
                    <button
                        onClick={clearAll}
                        className="text-white hover:text-gray-200 transition-colors"
                        title="Notīrīt visu"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                <p className="text-xs text-white/80 mt-1">
                    {selectedCompanies.length} no 5 uzņēmumiem
                </p>
            </div>

            {/* Company List */}
            <div className="p-3 max-h-64 overflow-y-auto">
                <div className="space-y-2">
                    {selectedCompanies.map((company) => (
                        <div
                            key={company.regcode}
                            className="flex items-center justify-between p-2 bg-gray-50 rounded hover:bg-gray-100 transition-colors group"
                        >
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-gray-900 truncate">
                                    {company.name}
                                </p>
                                <p className="text-xs text-gray-500">{company.regcode}</p>
                            </div>
                            <button
                                onClick={() => removeCompany(company.regcode)}
                                className="ml-2 text-gray-400 hover:text-red-600 transition-colors opacity-0 group-hover:opacity-100"
                                title="Noņemt"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-gray-200 bg-gray-50 rounded-b-lg">
                <button
                    onClick={handleOpenComparison}
                    disabled={selectedCompanies.length < 2}
                    className={`w-full py-2 px-4 rounded-lg font-medium transition-all ${selectedCompanies.length >= 2
                            ? 'bg-primary text-white hover:bg-primary-dark shadow-sm hover:shadow'
                            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                        }`}
                >
                    {selectedCompanies.length < 2
                        ? 'Izvēlies vismaz 2 uzņēmumus'
                        : 'Atvērt salīdzinājumu'}
                </button>
            </div>
        </div>
    );
}
