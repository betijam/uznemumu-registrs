import Navbar from "@/components/Navbar";
import { notFound } from "next/navigation";
import { Link } from "@/i18n/routing";
import CompanySearchBar from "@/components/CompanySearchBar";
import { getTranslations } from "next-intl/server";

// Cache configuration
const CACHE_CONFIG = { next: { revalidate: 1800 } }; // 30 min cache

// Data Fetching
async function getPersonProfile(id: string) {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    try {
        const res = await fetch(`${API_BASE_URL}/person/${id}`, CACHE_CONFIG);
        if (!res.ok) return null;
        return res.json();
    } catch (e) {
        console.error('Error fetching person profile:', e);
        return null;
    }
}

// Currency formatting
function formatCurrency(value: number | null | undefined): string {
    if (value === null || value === undefined || value === 0) return '-';
    const absValue = Math.abs(value);
    const sign = value < 0 ? '-' : '';
    if (absValue >= 1000000) {
        return `${sign}${(absValue / 1000000).toFixed(1)} M€`;
    } else if (absValue >= 1000) {
        return `${sign}${Math.round(absValue / 1000)} k€`;
    }
    return `${sign}${Math.round(absValue)} €`;
}


// Role badge helper
function getRoleBadge(role: string, t: any, position?: string) {
    switch (role) {
        case 'officer':
            return { text: position || t('position'), color: 'bg-blue-100 text-blue-700' };
        case 'member':
            return { text: t('beneficial_owner'), color: 'bg-green-100 text-green-700' };
        case 'ubo':
            return { text: t('beneficial_owner'), color: 'bg-yellow-100 text-yellow-700' };
        default:
            return { text: t('position'), color: 'bg-gray-100 text-gray-700' };
    }
}

// Initials helper
function getInitials(name: string): string {
    return name
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .substring(0, 2);
}


export async function generateMetadata({ params }: { params: Promise<{ id: string, locale: string }> }) {
    const { id, locale } = await params;
    const person = await getPersonProfile(id);
    const t = await getTranslations({ locale, namespace: 'PersonPage' });
    if (!person) return { title: t('not_found') };
    return {
        title: `${person.full_name} - ${t('positions')}`,
        description: `${person.full_name}`,
        robots: 'noindex, nofollow', // GDPR: Block from search engines
    };
}

export default async function PersonPage({ params }: { params: Promise<{ id: string, locale: string }> }) {
    const { id, locale } = await params;
    const person = await getPersonProfile(id);
    const t = await getTranslations({ locale, namespace: 'PersonPage' });

    if (!person) {
        notFound();
    }

    // Separate companies into active and historical
    const activeCompanies = person.companies.filter((c: any) => c.is_active);
    const historicalCompanies = person.companies.filter((c: any) => !c.is_active);

    return (
        <div className="min-h-screen bg-background pb-12">
            <Navbar />

            {/* Header */}
            <div className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    {/* Search Bar */}
                    <div className="mb-4 max-w-md">
                        <CompanySearchBar />
                    </div>

                    {/* Risk Badges */}
                    {(person.risk_badges.sanctions || person.risk_badges.insolvency || person.risk_badges.tax_debt) && (
                        <div className="flex flex-wrap gap-2 mb-3">
                            {person.risk_badges.sanctions && (
                                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-300">
                                    🛑 {t('sanctions')}
                                </span>
                            )}
                            {person.risk_badges.insolvency && (
                                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-orange-100 text-orange-800 border border-orange-300">
                                    ⛔ {t('insolvency')}
                                </span>
                            )}
                            {person.risk_badges.tax_debt && (
                                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800 border border-yellow-300">
                                    ⚠️ {t('tax_debt')}
                                </span>
                            )}
                        </div>
                    )}

                    {/* Name */}
                    <h1 className="text-4xl font-bold text-primary mb-2">{person.full_name}</h1>

                    {/* Details Row */}
                    <div className="flex flex-wrap gap-6 text-sm text-gray-600 mb-4">
                        <span className="flex items-center gap-1">
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2" />
                            </svg>
                            {t('person_code')}: {person.person_code_masked}
                        </span>
                        {person.birth_date && (
                            <span className="flex items-center gap-1">
                                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                                {t('birth_date')}: {new Date(person.birth_date).toLocaleDateString('lv-LV')}
                            </span>
                        )}
                        <span className="flex items-center gap-1">
                            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {t('nationality')}: {person.nationality === 'LV' ? t('latvia') : person.nationality}
                        </span>
                    </div>
                </div>
            </div>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
                {/* KPI Dashboard */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
                    <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
                        <div className="text-sm text-gray-500 mb-1">{t('active_companies')}</div>
                        <div className="text-2xl font-bold text-primary">{person.kpi.active_companies_count}</div>
                    </div>
                    <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
                        <div className="text-sm text-gray-500 mb-1">{t('historical_companies')}</div>
                        <div className="text-2xl font-bold text-gray-700">{person.kpi.historical_companies_count}</div>
                    </div>
                    <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
                        <div className="text-sm text-gray-500 mb-1">{t('total_turnover')}</div>
                        <div className="text-2xl font-bold text-success">{formatCurrency(person.kpi.total_turnover_managed)}</div>
                    </div>
                    <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
                        <div className="text-sm text-gray-500 mb-1">{t('total_employees')}</div>
                        <div className="text-2xl font-bold text-gray-700">{person.kpi.total_employees_managed || 0}</div>
                    </div>
                    <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
                        <div className="text-sm text-gray-500 mb-1">{t('capital_share_value')}</div>
                        <div className="text-2xl font-bold text-blue-600">{formatCurrency(person.kpi.capital_share_value)}</div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Companies List - Takes 2 columns */}
                    <div className="lg:col-span-2">
                        <div className="bg-white rounded-lg shadow-md overflow-hidden">
                            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                                <h2 className="text-xl font-bold text-primary">{t('related_companies')}</h2>
                            </div>

                            {/* Tabs */}
                            <div className="border-b border-gray-200">
                                <nav className="flex -mb-px">
                                    <div className="px-6 py-3 border-b-2 border-primary font-medium text-primary text-sm">
                                        {t('active_tab')} ({activeCompanies.length})
                                    </div>
                                    {historicalCompanies.length > 0 && (
                                        <div className="px-6 py-3 text-gray-500 hover:text-gray-700 text-sm cursor-not-allowed">
                                            {t('historical_tab')} ({historicalCompanies.length})
                                        </div>
                                    )}
                                </nav>
                            </div>

                            {/* Active Companies Table */}
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('company')}</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('role')}</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('shares')}</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('BenchmarkPage.turnover')}</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{t('status')}</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {activeCompanies.length === 0 ? (
                                            <tr>
                                                <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                                                    Nav aktīvu uzņ ēmumu
                                                </td>
                                            </tr>
                                        ) : (
                                            activeCompanies.map((company: any) => {
                                                const badge = getRoleBadge(company.role, t, company.position);
                                                return (
                                                    <tr key={company.regcode} className="hover:bg-gray-50">
                                                        <td className="px-6 py-4">
                                                            <Link href={`/company/${company.regcode}`} className="text-primary hover:underline font-medium">
                                                                {company.name}
                                                            </Link>
                                                            <div className="text-xs text-gray-500">{t('reg_no')} {company.regcode}</div>
                                                        </td>
                                                        <td className="px-6 py-4">
                                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badge.color}`}>
                                                                {badge.text}
                                                            </span>
                                                        </td>
                                                        <td className="px-6 py-4 text-sm text-gray-900">
                                                            {company.share_percent ? `${company.share_percent}%` : '-'}
                                                        </td>
                                                        <td className="px-6 py-4 text-sm text-gray-900">
                                                            {company.finances?.turnover ? formatCurrency(company.finances.turnover) : '-'}
                                                        </td>
                                                        <td className="px-6 py-4">
                                                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${company.status === 'active' ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'
                                                                }`}>
                                                                {company.status === 'active' ? t('active') : t('liquidated')}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                );
                                            })
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    {/* Collaboration Network - Sidebar */}
                    <div className="lg:col-span-1">
                        <div className="bg-white rounded-lg shadow-md overflow-hidden">
                            <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                                <h2 className="text-lg font-bold text-primary">{t('collaboration_network')}</h2>
                                <p className="text-xs text-gray-500 mt-1">{t('collaboration_desc')}</p>
                            </div>
                            <div className="p-4">
                                {person.collaboration_network.length === 0 ? (
                                    <p className="text-sm text-gray-500 text-center py-4">{t('no_collaboration_partners')}</p>
                                ) : (
                                    <div className="space-y-4">
                                        {person.collaboration_network.map((collab: any) => (
                                            <div key={collab.person_id} className="group relative">
                                                <Link
                                                    href={`/person/${collab.person_id}`}
                                                    className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 transition-colors"
                                                >
                                                    {/* Avatar */}
                                                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-sm">
                                                        {getInitials(collab.name)}
                                                    </div>

                                                    {/* Content */}
                                                    <div className="flex-1 min-w-0">
                                                        <div className="font-medium text-sm text-primary truncate">
                                                            {collab.name}
                                                        </div>
                                                        <div className="text-xs text-gray-500">
                                                            {t('companies_together', { count: collab.companies_together })}
                                                        </div>
                                                    </div>
                                                </Link>

                                                {/* Tooltip - Popups on hover */}
                                                <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block w-64 p-3 bg-gray-900 text-white text-xs rounded shadow-lg z-10 pointer-events-none">
                                                    <div className="font-semibold mb-1 border-b border-gray-700 pb-1">{t('common_companies')}</div>
                                                    <div className="leading-relaxed">
                                                        {collab.company_names || t('no_data')}
                                                    </div>
                                                    {/* Arrow */}
                                                    <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[6px] border-t-gray-900"></div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
