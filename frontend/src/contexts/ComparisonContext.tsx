"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';

interface Company {
    regcode: string;
    name: string;
}

interface ComparisonContextType {
    selectedCompanies: Company[];
    addCompany: (company: Company) => void;
    removeCompany: (regcode: string) => void;
    clearAll: () => void;
    isSelected: (regcode: string) => boolean;
    canAddMore: boolean;
}

const ComparisonContext = createContext<ComparisonContextType | undefined>(undefined);

const MAX_COMPANIES = 5;
const STORAGE_KEY = 'benchmark_comparison_cart';

export function ComparisonProvider({ children }: { children: React.ReactNode }) {
    const [selectedCompanies, setSelectedCompanies] = useState<Company[]>([]);

    // Load from localStorage on mount
    useEffect(() => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) {
                const parsed = JSON.parse(stored);
                setSelectedCompanies(parsed);
            }
        } catch (error) {
            console.error('Error loading comparison cart:', error);
        }
    }, []);

    // Save to localStorage whenever selection changes
    useEffect(() => {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(selectedCompanies));
        } catch (error) {
            console.error('Error saving comparison cart:', error);
        }
    }, [selectedCompanies]);

    const addCompany = (company: Company) => {
        if (selectedCompanies.length >= MAX_COMPANIES) {
            return; // Already at max
        }
        if (!selectedCompanies.find(c => c.regcode === company.regcode)) {
            setSelectedCompanies([...selectedCompanies, company]);
        }
    };

    const removeCompany = (regcode: string) => {
        setSelectedCompanies(selectedCompanies.filter(c => c.regcode !== regcode));
    };

    const clearAll = () => {
        setSelectedCompanies([]);
    };

    const isSelected = (regcode: string) => {
        return selectedCompanies.some(c => c.regcode === regcode);
    };

    const canAddMore = selectedCompanies.length < MAX_COMPANIES;

    return (
        <ComparisonContext.Provider
            value={{
                selectedCompanies,
                addCompany,
                removeCompany,
                clearAll,
                isSelected,
                canAddMore
            }}
        >
            {children}
        </ComparisonContext.Provider>
    );
}

export function useComparison() {
    const context = useContext(ComparisonContext);
    if (context === undefined) {
        throw new Error('useComparison must be used within a ComparisonProvider');
    }
    return context;
}
