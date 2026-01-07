'use client';

import { Link } from '@/i18n/routing';

interface SubIndustry {
    code: string;
    name: string;
    turnover: number | null;
    formatted_turnover: string | null;
    share: number;
    companies?: number;
}

interface Props {
    subIndustries: SubIndustry[];
}

export default function SubIndustryList({ subIndustries }: Props) {
    if (!subIndustries || subIndustries.length === 0) {
        return null;
    }

    return (
        <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100 h-full">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Nozares Struktūra</h3>
            <p className="text-sm text-gray-500 mb-6">Lielākās apakšnozares pēc apgrozījuma</p>

            <div className="space-y-4">
                {subIndustries.map((item, idx) => (
                    <Link
                        key={item.code}
                        href={`/industries/${item.code}`}
                        className="group block hover:bg-gray-50 rounded-lg p-2 -mx-2 transition-colors"
                    >
                        <div className="flex justify-between items-center mb-1">
                            <div className="flex items-center min-w-0 flex-1 mr-4">
                                <span className="text-xs font-mono text-gray-400 w-10">{item.code}</span>
                                <span className="text-sm font-medium text-gray-700 truncate group-hover:text-blue-600 transition-colors">
                                    {item.name}
                                </span>
                            </div>
                            <div className="text-right flex-shrink-0">
                                <span className="block text-sm font-bold text-gray-900">
                                    {item.formatted_turnover}
                                </span>
                                {item.companies && (
                                    <span className="text-[10px] text-gray-400">
                                        {item.companies} uzņ.
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                            <div
                                className="bg-blue-500 h-1.5 rounded-full transition-all duration-500"
                                style={{ width: `${Math.min(item.share, 100)}%` }}
                            />
                        </div>
                        <div className="flex justify-end mt-0.5">
                            <span className="text-[10px] text-gray-400 font-medium">
                                {item.share}% no kopējā
                            </span>
                        </div>
                    </Link>
                ))}
            </div>
        </div>
    );
}

