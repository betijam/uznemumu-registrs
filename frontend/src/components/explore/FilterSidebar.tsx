"use client";

import React, { useState, useEffect } from "react";
// Would usually import debounced search but doing simple now

interface FilterSidebarProps {
    filters: any;
    onFilterChange: (newFilters: any) => void;
}

export default function FilterSidebar({ filters, onFilterChange }: FilterSidebarProps) {
    const [localFilters, setLocalFilters] = useState(filters);

    useEffect(() => {
        setLocalFilters(filters);
    }, [filters]);

    const handleChange = (key: string, value: any) => {
        const newFilters = { ...localFilters, [key]: value };
        setLocalFilters(newFilters);
        // Debounce could be here
        onFilterChange(newFilters);
    };

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6 space-y-8 sticky top-24">
            <div>
                <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">Statuss</h3>
                <div className="space-y-2">
                    <label className="flex items-center">
                        <input
                            type="radio"
                            name="status"
                            className="text-purple-600 focus:ring-purple-500 h-4 w-4"
                            checked={localFilters.status === 'active'}
                            onChange={() => handleChange('status', 'active')}
                        />
                        <span className="ml-2 text-sm text-gray-700">Aktīvs</span>
                    </label>
                    <label className="flex items-center">
                        <input
                            type="radio"
                            name="status"
                            className="text-purple-600 focus:ring-purple-500 h-4 w-4"
                            checked={localFilters.status === 'liquidated'}
                            onChange={() => handleChange('status', 'liquidated')}
                        />
                        <span className="ml-2 text-sm text-gray-700">Likvidēts</span>
                    </label>
                    <label className="flex items-center">
                        <input
                            type="radio"
                            name="status"
                            className="text-purple-600 focus:ring-purple-500 h-4 w-4"
                            checked={localFilters.status === 'all'}
                            onChange={() => handleChange('status', 'all')}
                        />
                        <span className="ml-2 text-sm text-gray-700">Visi</span>
                    </label>
                </div>
            </div>

            <div>
                <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">Reģions</h3>
                <input
                    type="text"
                    placeholder="Meklēt reģionu (Rīga...)"
                    className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-purple-500 focus:ring-purple-500"
                    value={localFilters.region || ""}
                    onChange={(e) => handleChange('region', e.target.value)}
                />
            </div>

            <div>
                <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">Nozare (NACE)</h3>
                <input
                    type="text"
                    placeholder="Kods (piem. 62.0)"
                    className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-purple-500 focus:ring-purple-500"
                    value={localFilters.nace || ""}
                    onChange={(e) => handleChange('nace', e.target.value)}
                />
            </div>

            <div className="pt-4 border-t border-gray-100">
                <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">Finanšu Filtri</h3>

                <div className="mb-4">
                    <label className="block text-xs font-medium text-gray-700 mb-1">Min. Apgrozījums (€)</label>
                    <input
                        type="number"
                        className="w-full text-sm border-gray-300 rounded-md shadow-sm"
                        placeholder="0"
                        value={localFilters.min_turnover || ""}
                        onChange={(e) => handleChange('min_turnover', e.target.value)}
                    />
                </div>

                <div className="mb-4">
                    <label className="block text-xs font-medium text-gray-700 mb-1">Min. Darbinieki</label>
                    <input
                        type="number"
                        className="w-full text-sm border-gray-300 rounded-md shadow-sm"
                        placeholder="0"
                        value={localFilters.min_employees || ""}
                        onChange={(e) => handleChange('min_employees', e.target.value)}
                    />
                </div>
            </div>

            <div className="pt-4 border-t border-gray-100 space-y-2">
                <label className="flex items-center">
                    <input
                        type="checkbox"
                        className="rounded text-purple-600 focus:ring-purple-500 h-4 w-4"
                        checked={localFilters.has_pvn || false}
                        onChange={(e) => handleChange('has_pvn', e.target.checked)}
                    />
                    <span className="ml-2 text-sm text-gray-700">PVN maksātājs</span>
                </label>
                <label className="flex items-center">
                    <input
                        type="checkbox"
                        className="rounded text-red-600 focus:ring-red-500 h-4 w-4"
                        checked={localFilters.has_sanctions || false}
                        onChange={(e) => handleChange('has_sanctions', e.target.checked)}
                    />
                    <span className="ml-2 text-sm text-gray-700">Ir sankcijas</span>
                </label>
            </div>

            <button
                className="w-full py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                onClick={() => onFilterChange({ status: 'active', page: 1 })}
            >
                Notīrīt filtrus
            </button>
        </div>
    );
}
