"use client";

import React, { useState, useEffect, useRef } from "react";
import { useTranslations } from 'next-intl';

interface FilterSidebarProps {
    filters: any;
    onFilterChange: (newFilters: any) => void;
}

// NACE Multi-Selector Component
function NaceSelector({ value, onChange }: { value: string[], onChange: (val: string[]) => void }) {
    const t = useTranslations('Analytics.filters');
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<any[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const wrapperRef = useRef<HTMLDivElement>(null);

    // Ensure value is always array
    const selectedCodes = Array.isArray(value) ? value : (value ? [value] : []);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [wrapperRef]);

    const handleSearch = async (val: string) => {
        setQuery(val);
        setIsOpen(true);
        if (val.length < 1) {
            setResults([]);
            return;
        }

        setLoading(true);
        try {
            const res = await fetch(`/api/industries/search?q=${encodeURIComponent(val)}&limit=10`);
            if (res.ok) {
                const json = await res.json();
                setResults(json.results || []);
            }
        } catch (e) {
            console.error("NACE Search Error", e);
        } finally {
            setLoading(false);
        }
    };

    const handleSelect = (item: any) => {
        // Prevent duplicates
        if (!selectedCodes.includes(item.code)) {
            onChange([...selectedCodes, item.code]);
        }
        setQuery(""); // Clear query after select
        setIsOpen(false);
    };

    const removeCode = (codeToRemove: string) => {
        onChange(selectedCodes.filter(c => c !== codeToRemove));
    };

    return (
        <div className="relative space-y-2" ref={wrapperRef}>
            {/* Selected Chips */}
            {selectedCodes.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-2">
                    {selectedCodes.map(code => (
                        <span key={code} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                            {code}
                            <button
                                type="button"
                                onClick={() => removeCode(code)}
                                className="ml-1 text-purple-600 hover:text-purple-800 focus:outline-none"
                            >
                                ×
                            </button>
                        </span>
                    ))}
                </div>
            )}

            <input
                type="text"
                placeholder={t('industry_placeholder')}
                className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-purple-500 focus:ring-purple-500"
                value={query}
                onChange={(e) => handleSearch(e.target.value)}
                onFocus={() => { setIsOpen(true); if (query) handleSearch(query); }}
            />

            {isOpen && (results.length > 0 || loading) && (
                <div className="absolute z-50 w-full bg-white mt-1 border border-gray-100 rounded-md shadow-lg max-h-60 overflow-auto">
                    {loading && <div className="p-2 text-xs text-gray-400">{t('searching')}</div>}
                    {!loading && results.map((item) => (
                        <div
                            key={item.code}
                            className="px-4 py-2 hover:bg-purple-50 cursor-pointer text-sm border-b border-gray-50 last:border-0"
                            onClick={() => handleSelect(item)}
                        >
                            <div className="font-semibold text-gray-900">{item.code}</div>
                            <div className="text-gray-600 text-xs truncate">{item.name}</div>
                        </div>
                    ))}
                    {!loading && results.length === 0 && query.length > 1 && (
                        <div className="p-2 text-xs text-gray-400">{t('not_found')}</div>
                    )}
                </div>
            )}
        </div>
    );
}

export default function FilterSidebar({ filters, onFilterChange }: FilterSidebarProps) {
    const t = useTranslations('Analytics.filters');
    const tRegions = useTranslations('Analytics.regions');
    const [localFilters, setLocalFilters] = useState(filters);

    const REGIONS = [
        { label: tRegions('all'), value: "" },
        { label: tRegions('riga'), value: "Rīga" },
        { label: tRegions('pieriga'), value: "Pierīga" },
        { label: tRegions('vidzeme'), value: "Vidzeme" },
        { label: tRegions('kurzeme'), value: "Kurzeme" },
        { label: tRegions('zemgale'), value: "Zemgale" },
        { label: tRegions('latgale'), value: "Latgale" },
        { label: tRegions('jurmala'), value: "Jūrmala" },
        { label: tRegions('liepaja'), value: "Liepāja" },
        { label: tRegions('daugavpils'), value: "Daugavpils" },
        { label: tRegions('jelgava'), value: "Jelgava" },
        { label: tRegions('valmiera'), value: "Valmiera" },
        { label: tRegions('ventspils'), value: "Ventspils" },
        { label: tRegions('rezekne'), value: "Rēzekne" }
    ];

    useEffect(() => {
        setLocalFilters(filters);
    }, [filters]);

    const handleChange = (key: string, value: any) => {
        const newFilters = { ...localFilters, [key]: value };
        setLocalFilters(newFilters);
        // Direct update for selects/checkboxes
        if (key !== 'min_turnover' && key !== 'min_employees') {
            onFilterChange(newFilters);
        }
    };

    // Separate Apply for text inputs
    const applyInputs = () => {
        onFilterChange(localFilters);
    };

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6 space-y-8 sticky top-24">
            <div>
                <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">{t('status_label')}</h3>
                <div className="space-y-2">
                    <label className="flex items-center cursor-pointer group">
                        <input
                            type="radio"
                            name="status"
                            className="text-purple-600 focus:ring-purple-500 h-4 w-4 cursor-pointer"
                            checked={localFilters.status === 'active'}
                            onChange={() => handleChange('status', 'active')}
                        />
                        <span className="ml-2 text-sm text-gray-700 group-hover:text-purple-600">{t('status_active')}</span>
                    </label>
                    <label className="flex items-center cursor-pointer group">
                        <input
                            type="radio"
                            name="status"
                            className="text-purple-600 focus:ring-purple-500 h-4 w-4 cursor-pointer"
                            checked={localFilters.status === 'liquidated'}
                            onChange={() => handleChange('status', 'liquidated')}
                        />
                        <span className="ml-2 text-sm text-gray-700 group-hover:text-purple-600">{t('status_liquidated')}</span>
                    </label>
                    <label className="flex items-center cursor-pointer group">
                        <input
                            type="radio"
                            name="status"
                            className="text-purple-600 focus:ring-purple-500 h-4 w-4 cursor-pointer"
                            checked={localFilters.status === 'all'}
                            onChange={() => handleChange('status', 'all')}
                        />
                        <span className="ml-2 text-sm text-gray-700 group-hover:text-purple-600">{t('status_all')}</span>
                    </label>
                </div>
            </div>

            <div>
                <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">{t('region_label')}</h3>
                <div className="relative">
                    <select
                        className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-purple-500 focus:ring-purple-500 appearance-none bg-white py-2 pl-3 pr-10"
                        value={localFilters.region || ""}
                        onChange={(e) => handleChange("region", e.target.value)}
                    >
                        {REGIONS.map((r) => (
                            <option key={r.value || "all"} value={r.value}>{r.label}</option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            <div>
                <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">{t('industry_label')}</h3>
                <NaceSelector
                    value={localFilters.nace}
                    onChange={(val) => handleChange("nace", val)}
                />
                <p className="text-xs text-gray-400 mt-1">{t('industry_hint')}</p>
            </div>

            <div className="pt-4 border-t border-gray-100">
                <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">{t('finance_label')}</h3>

                <div className="mb-4">
                    <label className="block text-xs font-medium text-gray-700 mb-1">{t('min_turnover')}</label>
                    <div className="flex gap-2">
                        <input
                            type="number"
                            className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-purple-500 focus:ring-purple-500"
                            placeholder="0"
                            value={localFilters.min_turnover || ""}
                            onChange={(e) => {
                                const val = e.target.value;
                                setLocalFilters({ ...localFilters, min_turnover: val });
                            }}
                            onBlur={applyInputs}
                            onKeyDown={(e) => e.key === 'Enter' && applyInputs()}
                        />
                    </div>
                </div>

                <div className="mb-4">
                    <label className="block text-xs font-medium text-gray-700 mb-1">{t('min_employees')}</label>
                    <input
                        type="number"
                        className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-purple-500 focus:ring-purple-500"
                        placeholder="0"
                        value={localFilters.min_employees || ""}
                        onChange={(e) => {
                            const val = e.target.value;
                            setLocalFilters({ ...localFilters, min_employees: val });
                        }}
                        onBlur={applyInputs}
                        onKeyDown={(e) => e.key === 'Enter' && applyInputs()}
                    />
                </div>
            </div>

            <div className="pt-4 border-t border-gray-100 space-y-2">
                <label className="flex items-center cursor-pointer">
                    <input
                        type="checkbox"
                        className="rounded text-purple-600 focus:ring-purple-500 h-4 w-4 cursor-pointer"
                        checked={localFilters.has_pvn || false}
                        onChange={(e) => handleChange('has_pvn', e.target.checked)}
                    />
                    <span className="ml-2 text-sm text-gray-700">{t('pvn_payer')}</span>
                </label>
                <label className="flex items-center cursor-pointer">
                    <input
                        type="checkbox"
                        className="rounded text-red-600 focus:ring-red-500 h-4 w-4 cursor-pointer"
                        checked={localFilters.has_sanctions || false}
                        onChange={(e) => handleChange('has_sanctions', e.target.checked)}
                    />
                    <span className="ml-2 text-sm text-gray-700">{t('has_sanctions')}</span>
                </label>
            </div>

            <button
                className="w-full py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                onClick={() => onFilterChange({ status: 'active', page: 1, nace: [], region: '', min_turnover: '', min_employees: '', has_pvn: false, has_sanctions: false })}
            >
                {t('clear_filters')}
            </button>
        </div>
    );
}
