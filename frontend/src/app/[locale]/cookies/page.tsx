
import { useTranslations } from 'next-intl';

export default function CookiePolicyPage() {
    const t = useTranslations('CookiePolicy');


    return (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
            <h1 className="text-3xl font-bold mb-4">{t('title')}</h1>

            <p className="text-sm text-gray-500 mb-8">{t('last_updated')}: {t('date')}</p>

            <p className="mb-4">{t('intro')}</p>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">{t('what_are.title')}</h2>
                <p>{t('what_are.content')}</p>
            </section>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">{t('why_use.title')}</h2>
                <p className="mb-4">{t('why_use.intro')}</p>
                <ul className="list-disc pl-5 space-y-2">
                    <li dangerouslySetInnerHTML={{ __html: t.raw('why_use.list_1') }} />
                    <li dangerouslySetInnerHTML={{ __html: t.raw('why_use.list_2') }} />
                    <li dangerouslySetInnerHTML={{ __html: t.raw('why_use.list_3') }} />
                </ul>
            </section>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">{t('which_cookies.title')}</h2>
                <p className="mb-4">{t('which_cookies.intro')}</p>

                {/* Type A */}
                <h3 className="text-xl font-medium mb-2">{t('which_cookies.type_a_title')}</h3>
                <p className="mb-4">{t('which_cookies.type_a_desc')}</p>
                <div className="overflow-x-auto mb-6">
                    <table className="min-w-full bg-white border border-gray-200 text-sm">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-4 py-2 text-left border-b font-semibold">{t('which_cookies.table_headers.name')}</th>
                                <th className="px-4 py-2 text-left border-b font-semibold">{t('which_cookies.table_headers.provider')}</th>
                                <th className="px-4 py-2 text-left border-b font-semibold">{t('which_cookies.table_headers.purpose')}</th>
                                <th className="px-4 py-2 text-left border-b font-semibold">{t('which_cookies.table_headers.expiry')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td className="px-4 py-2 border-b font-mono">c360_free_views</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.cookies.c360_free_views.provider')}</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.cookies.c360_free_views.purpose')}</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.cookies.c360_free_views.expiry')}</td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 border-b font-mono">c360_cookie_consent</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.cookies.c360_cookie_consent.provider')}</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.cookies.c360_cookie_consent.purpose')}</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.cookies.c360_cookie_consent.expiry')}</td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 border-b font-mono">{t('which_cookies.cookies.token_session.name')}</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.cookies.token_session.provider')}</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.cookies.token_session.purpose')}</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.cookies.token_session.expiry')}</td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 border-b font-mono">{t('which_cookies.cookies.csrf.name')}</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.cookies.csrf.provider')}</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.cookies.csrf.purpose')}</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.cookies.csrf.expiry')}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                {/* Type B */}
                <h3 className="text-xl font-medium mb-2">{t('which_cookies.type_b_title')}</h3>
                <p className="mb-4">{t('which_cookies.type_b_desc')}</p>
                <div className="overflow-x-auto mb-6">
                    <table className="min-w-full bg-white border border-gray-200 text-sm">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-4 py-2 text-left border-b font-semibold">{t('which_cookies.third_party_headers.name')}</th>
                                <th className="px-4 py-2 text-left border-b font-semibold">{t('which_cookies.third_party_headers.provider')}</th>
                                <th className="px-4 py-2 text-left border-b font-semibold">{t('which_cookies.third_party_headers.purpose')}</th>
                                <th className="px-4 py-2 text-left border-b font-semibold">{t('which_cookies.third_party_headers.link')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td className="px-4 py-2 border-b font-mono">{t('which_cookies.third_party_cookies.google.name')}</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.third_party_cookies.google.provider')}</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.third_party_cookies.google.purpose')}</td>
                                <td className="px-4 py-2 border-b">
                                    <a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                        {t('which_cookies.third_party_cookies.google.policy_name')}
                                    </a>
                                </td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 border-b font-mono">{t('which_cookies.third_party_cookies.linkedin.name')}</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.third_party_cookies.linkedin.provider')}</td>
                                <td className="px-4 py-2 border-b">{t('which_cookies.third_party_cookies.linkedin.purpose')}</td>
                                <td className="px-4 py-2 border-b">
                                    <a href="https://www.linkedin.com/legal/cookie-policy" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                        {t('which_cookies.third_party_cookies.linkedin.policy_name')}
                                    </a>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                {/* Type C */}
                <h3 className="text-xl font-medium mb-2">{t('which_cookies.type_c_title')}</h3>
                <p>{t('which_cookies.type_c_desc')}</p>
            </section>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">{t('manage.title')}</h2>
                <p className="mb-2">{t('manage.p1')}</p>
                <p className="mb-2">{t('manage.p2')}</p>
                <pre className="bg-gray-100 p-4 rounded mb-4 whitespace-pre-wrap font-sans text-sm">
                    {t('manage.list')}
                </pre>
                <p className="bg-yellow-50 p-4 rounded border border-yellow-200 text-yellow-800" dangerouslySetInnerHTML={{ __html: t.raw('manage.warning') }} />
            </section>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">{t('changes.title')}</h2>
                <p>{t('changes.content')}</p>
            </section>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">{t('contact.title')}</h2>
                <p className="mb-4">{t('contact.content')}</p>
                <ul className="list-none space-y-1">
                    <li>{t('contact.email')}</li>
                    <li>{t('contact.address')}</li>
                </ul>
            </section>
        </div>
    );
}
