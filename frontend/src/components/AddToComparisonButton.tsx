"use client";

import { useComparison } from '@/contexts/ComparisonContext';

interface AddToComparisonButtonProps {
    company: {
        regcode: string;
        name: string;
    };
}

export default function AddToComparisonButton({ company }: AddToComparisonButtonProps) {
    const { addCompany, removeCompany, isSelected, canAddMore } = useComparison();
    const selected = isSelected(company.regcode.toString());

    const handleToggle = () => {
        if (selected) {
            removeCompany(company.regcode.toString());
        } else {
            if (canAddMore) {
                addCompany({
                    regcode: company.regcode.toString(),
                    name: company.name
                });
            }
        }
    };

    return (
        <button
            onClick={handleToggle}
            disabled={!selected && !canAddMore}
            className={`inline-flex items-center gap-2 px-4 py-2 border rounded-lg text-sm font-medium transition-colors shadow-sm ${selected
                    ? 'border-primary bg-primary text-white hover:bg-primary-dark'
                    : canAddMore
                        ? 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
                        : 'border-gray-200 text-gray-400 bg-gray-50 cursor-not-allowed'
                }`}
            title={!selected && !canAddMore ? 'Maksimālais uzņēmumu skaits salīdzināšanai sasniegts (5)' : ''}
        >
            {selected ? (
                <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Pievienots salīdzināšanai
                </>
            ) : (
                <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    Pievienot salīdzināšanai
                </>
            )}
        </button>
    );
}
