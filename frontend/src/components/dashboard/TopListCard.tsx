import Link from 'next/link';
import React from 'react';
import { formatCompanyName } from '@/utils/formatCompanyName';

interface TopItem {
    name: string;
    name_in_quotes?: string | null;
    type?: string | null;
    type_text?: string | null;
    regcode: number;
    value: number;
    industry?: string;
}

interface TopListCardProps {
    title: string;
    subtitle?: string;
    icon: React.ReactNode;
    items: TopItem[];
    valueFormatter: (val: number) => string;
    linkTo?: string;
    colorClass?: string;
}

export default function TopListCard({ title, subtitle, icon, items, valueFormatter, linkTo, colorClass = "text-blue-600" }: TopListCardProps) {
    return (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 flex flex-col h-full">
            <div className="flex items-center gap-3 mb-4">
                <div className={`p-2 rounded-lg bg-gray-50 ${colorClass}`}>
                    {icon}
                </div>
                <div>
                    <h3 className="font-semibold text-gray-900">{title}</h3>
                    {subtitle && <p className="text-xs text-gray-400">{subtitle}</p>}
                </div>
            </div>

            <div className="flex-1 space-y-5">
                {items.slice(0, 3).map((item, idx) => (
                    <div key={item.regcode} className="group flex items-start justify-between">
                        <div className="flex gap-4">
                            <span className="text-sm font-bold text-orange-400 mt-0.5">{idx + 1}</span>
                            <div>
                                <Link href={`/company/${item.regcode}`} className="font-medium text-gray-900 group-hover:text-blue-600 transition-colors line-clamp-1">
                                    {formatCompanyName(item)}
                                </Link>
                                {item.industry && (
                                    <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{item.industry}</p>
                                )}
                            </div>
                        </div>
                        <div className="text-right font-bold text-gray-900 whitespace-nowrap">
                            {valueFormatter(item.value)}
                        </div>
                    </div>
                ))}
            </div>

            {linkTo && (
                <div className="mt-6 pt-4 border-t border-gray-50 text-center">
                    <Link href={linkTo} className="text-sm font-medium text-purple-600 hover:text-purple-700 transition-colors">
                        Skatīt visus →
                    </Link>
                </div>
            )}
        </div>
    );
}
