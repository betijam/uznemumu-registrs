import Navbar from "@/components/Navbar";
import SearchInput from "@/components/SearchInput";
import Link from "next/link";
import { formatCompanyName } from "@/utils/formatCompanyName";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

async function getCompanyResults(query: string) {
    try {
        const res = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(query)}`, {
            cache: "no-store",
        });
        if (!res.ok) return [];
        return res.json();
    } catch (e) {
        console.error("Company search error:", e);
        return [];
    }
}

async function getPersonResults(query: string) {
    try {
        const res = await fetch(`${API_BASE_URL}/search/persons?q=${encodeURIComponent(query)}`, {
            cache: "no-store",
        });
        if (!res.ok) return { persons: [], total: 0 };
        return res.json();
    } catch (e) {
        console.error("Person search error:", e);
        return { persons: [], total: 0 };
    }
}

export default async function SearchPage({
    searchParams,
}: {
    searchParams: Promise<{ q?: string; tab?: string }>;
}) {
    const { q, tab } = await searchParams;
    const query = q || "";
    const activeTab = tab || "all"; // 'all', 'companies', 'persons'

    // Fetch data in parallel
    const [companies, personData] = await Promise.all([
        query ? getCompanyResults(query) : Promise.resolve([]),
        query ? getPersonResults(query) : Promise.resolve({ persons: [], total: 0 })
    ]);

    const persons = personData.persons || [];
    const totalCompanies = companies.length;
    const totalPersons = personData.total;

    const hasResults = totalCompanies > 0 || totalPersons > 0;

    return (
        <div className="min-h-screen bg-background pb-12">
            <Navbar />

            {/* Search Header */}
            <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-30">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <h1 className="text-2xl font-bold text-primary mb-4">Meklēšana</h1>
                    <div className="max-w-3xl">
                        <SearchInput />
                    </div>
                </div>

                {/* Tabs */}
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-2">
                    <nav className="flex space-x-8" aria-label="Tabs">
                        <Link
                            href={`/search?q=${encodeURIComponent(query)}&tab=all`}
                            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'all'
                                    ? 'border-purple-500 text-purple-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            Visi
                        </Link>
                        <Link
                            href={`/search?q=${encodeURIComponent(query)}&tab=companies`}
                            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'companies'
                                    ? 'border-purple-500 text-purple-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            Uzņēmumi ({totalCompanies})
                        </Link>
                        <Link
                            href={`/search?q=${encodeURIComponent(query)}&tab=persons`}
                            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'persons'
                                    ? 'border-purple-500 text-purple-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            Personas ({totalPersons})
                        </Link>
                    </nav>
                </div>
            </div>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
                {!query ? (
                    <div className="text-center py-12">
                        <h3 className="text-lg font-medium text-gray-900">Ievadiet meklēšanas vaicājumu</h3>
                    </div>
                ) : !hasResults ? (
                    <div className="bg-white rounded-lg shadow-card p-12 text-center">
                        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                        <h3 className="mt-4 text-lg font-medium text-gray-900">Nav rezultātu</h3>
                        <p className="mt-2 text-sm text-gray-500">
                            Mēģiniet mainīt meklēšanas vaicājumu vai izmantojiet citus atslēgvārdus.
                        </p>
                    </div>
                ) : (
                    <div className="space-y-8">
                        {/* Companies List */}
                        {(activeTab === 'all' || activeTab === 'companies') && totalCompanies > 0 && (
                            <section>
                                {(activeTab === 'all') && (
                                    <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                                        Uzņēmumi
                                        <span className="ml-2 bg-gray-100 text-gray-600 text-xs py-0.5 px-2 rounded-full">{totalCompanies}</span>
                                    </h2>
                                )}
                                <div className="grid grid-cols-1 gap-4">
                                    {companies.map((company: any) => (
                                        <Link
                                            key={company.regcode}
                                            href={`/company/${company.regcode}`}
                                            className="block bg-white rounded-lg shadow-card hover:shadow-card-hover transition-all p-6 border border-gray-100 group"
                                        >
                                            <div className="flex items-start justify-between">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-3 mb-2">
                                                        <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0 text-purple-600 group-hover:bg-purple-600 group-hover:text-white transition-colors">
                                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                                                            </svg>
                                                        </div>
                                                        <div>
                                                            <h3 className="text-lg font-semibold text-gray-900 group-hover:text-purple-600 transition-colors">{formatCompanyName(company)}</h3>
                                                            <p className="text-sm text-gray-500">Reģ. Nr. {company.regcode}</p>
                                                        </div>
                                                    </div>
                                                    <div className="text-sm text-gray-600 ml-13 pl-0.5">
                                                        {company.address}
                                                    </div>
                                                </div>
                                                <div className="flex flex-col items-end gap-2">
                                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${company.status === 'active' ? 'bg-green-100 text-green-800' :
                                                            company.status === 'monitoring' ? 'bg-yellow-100 text-yellow-800' :
                                                                'bg-red-100 text-red-800'
                                                        }`}>
                                                        {company.status === 'active' ? 'AKTĪVS' : company.status === 'monitoring' ? 'MONITORINGS' : 'LIKVIDĒTS'}
                                                    </span>
                                                </div>
                                            </div>
                                        </Link>
                                    ))}
                                </div>
                            </section>
                        )}

                        {/* Persons List */}
                        {(activeTab === 'all' || activeTab === 'persons') && totalPersons > 0 && (
                            <section>
                                {(activeTab === 'all') && (
                                    <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                                        Personas
                                        <span className="ml-2 bg-gray-100 text-gray-600 text-xs py-0.5 px-2 rounded-full">{totalPersons}</span>
                                    </h2>
                                )}
                                <div className="grid grid-cols-1 gap-4">
                                    {persons.map((person: any) => (
                                        <Link
                                            key={person.person_id}
                                            href={`/person/${person.person_id}`}
                                            className="block bg-white rounded-lg shadow-card hover:shadow-card-hover transition-all p-6 border border-gray-100 group"
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-4">
                                                    <div className="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center flex-shrink-0 text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                                        </svg>
                                                    </div>
                                                    <div>
                                                        <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">{person.name}</h3>
                                                        <div className="flex items-center gap-3 text-sm text-gray-500">
                                                            <span>Personas kods: {person.person_code}</span>
                                                            {person.birth_date && (
                                                                <>
                                                                    <span className="w-1 h-1 bg-gray-300 rounded-full"></span>
                                                                    <span>Dz. dat: {person.birth_date}</span>
                                                                </>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="text-right">
                                                    <div className="text-sm font-medium text-gray-900">
                                                        {person.company_count} uzņēmumi
                                                    </div>
                                                    <div className="text-xs text-gray-500 mt-1 max-w-[200px] truncate">
                                                        {person.roles.join(", ")}
                                                    </div>
                                                </div>
                                            </div>
                                        </Link>
                                    ))}
                                </div>
                            </section>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}
