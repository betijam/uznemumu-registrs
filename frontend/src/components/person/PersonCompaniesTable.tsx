"use client";

import { Link } from "@/i18n/routing";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { formatCurrency } from "@/lib/utils";

interface Company {
    regcode: number;
    name: string;
    status: string;
    roles: Array<{
        type: string;
        position?: string;
        share_percent?: number;
        date_from?: string;
    }>;
    finances?: {
        turnover?: number;
    };
}

interface Props {
    activeCompanies: Company[];
}

export default function PersonCompaniesTable({ activeCompanies }: Props) {
    const t = useTranslations('PersonPage');
    const [showAllCompanies, setShowAllCompanies] = useState(false);

    if (activeCompanies.length === 0) {
        return (
            <div className="px-6 py-8 text-center text-gray-500">
                {t('no_active_companies')}
            </div>
        );
    }

    const displayedCompanies = showAllCompanies ? activeCompanies : activeCompanies.slice(0, 5);

    return (
        <div>
            <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('company')}</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('role')}</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('turnover')}</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {displayedCompanies.map((company) => (
                            <tr key={company.regcode} className="hover:bg-gray-50">
                                <td className="px-6 py-4">
                                    <Link href={`/company/${company.regcode}`} className="text-primary hover:underline font-medium">
                                        {company.name}
                                    </Link>
                                    <div className="text-xs text-gray-500">{t('reg_no')} {company.regcode}</div>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex flex-wrap gap-2">
                                        {company.roles.map((role, idx) => {
                                            let colorClass = "bg-gray-100 text-gray-700 border-gray-200";
                                            let text = t('position');

                                            if (role.type === 'officer') {
                                                colorClass = "bg-blue-50 text-blue-700 border-blue-200 border";
                                                text = role.position || t('officer');
                                            } else if (role.type === 'member') {
                                                colorClass = "bg-green-50 text-green-700 border-green-200 border";
                                                text = `${t('member')} ${role.share_percent ? role.share_percent + '%' : ''}`;
                                            } else if (role.type === 'ubo') {
                                                colorClass = "bg-yellow-50 text-yellow-700 border-yellow-200 border";
                                                text = t('ubo');
                                            }

                                            return (
                                                <span key={idx} className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium whitespace-nowrap ${colorClass}`}>
                                                    {text}
                                                    {role.date_from && <span className="ml-1 opacity-70 text-[10px]">({role.date_from.substring(0, 4)})</span>}
                                                </span>
                                            );
                                        })}
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-sm text-gray-900">
                                    {company.finances?.turnover ? formatCurrency(company.finances.turnover) : '-'}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Show More Button */}
            {activeCompanies.length > 5 && (
                <div className="px-6 py-3 border-t border-gray-100 bg-gray-50 text-center">
                    <button
                        onClick={() => setShowAllCompanies(!showAllCompanies)}
                        className="text-primary text-sm font-medium hover:underline focus:outline-none"
                    >
                        {showAllCompanies ? t('show_less') : t('show_more_count', { count: activeCompanies.length - 5 })}
                    </button>
                </div>
            )}
        </div>
    );
}
