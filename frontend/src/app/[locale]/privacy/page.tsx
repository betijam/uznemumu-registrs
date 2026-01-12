
import { useTranslations } from 'next-intl';

export default function PrivacyPage() {
    const t = useTranslations('Privacy');


    return (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
            <h1 className="text-3xl font-bold mb-4">{t('title')}</h1>

            <p className="text-sm text-gray-500 mb-8">{t('last_updated')}: {t('date')}</p>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">1. {t('general_info.title')}</h2>
                <p className="mb-4">{t('general_info.p1')}</p>
                <p className="mb-4">{t('general_info.p2')}</p>
                <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="font-semibold mb-2">{t('general_info.controller_title')}</p>
                    <ul className="list-none space-y-1">
                        <li>{t('general_info.name')}</li>
                        <li>{t('general_info.reg_no')}</li>
                        <li>{t('general_info.email')}</li>
                    </ul>
                </div>
            </section>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">2. {t('data_we_collect.title')}</h2>
                <p className="mb-4">{t('data_we_collect.intro')}</p>

                <h3 className="text-xl font-medium mb-2">{t('data_we_collect.section_a_title')}</h3>
                <p className="mb-2">{t('data_we_collect.section_a_desc')}</p>
                <ul className="list-disc pl-5 mb-4 space-y-1">
                    <li dangerouslySetInnerHTML={{ __html: t.raw('data_we_collect.list_email') }} />
                    <li dangerouslySetInnerHTML={{ __html: t.raw('data_we_collect.list_social') }} />
                </ul>
                <p className="text-sm bg-blue-50 p-2 rounded" dangerouslySetInnerHTML={{ __html: t.raw('data_we_collect.important_note') }} />

                <h3 className="text-xl font-medium mt-4 mb-2">{t('data_we_collect.section_b_title')}</h3>
                <p className="mb-2">{t('data_we_collect.section_b_desc')}</p>
                <ul className="list-disc pl-5 mb-4 space-y-1">
                    <li>{t('data_we_collect.list_tech_1')}</li>
                    <li>{t('data_we_collect.list_tech_2')}</li>
                    <li>{t('data_we_collect.list_tech_3')}</li>
                </ul>
            </section>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">3. {t('purpose.title')}</h2>
                <div className="overflow-x-auto">
                    <table className="min-w-full bg-white border border-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-4 py-2 text-left border-b">{t('purpose.table_col_1')}</th>
                                <th className="px-4 py-2 text-left border-b">{t('purpose.table_col_2')}</th>
                                <th className="px-4 py-2 text-left border-b">{t('purpose.table_col_3')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td className="px-4 py-2 border-b">{t('purpose.row_1_col_1')}</td>
                                <td className="px-4 py-2 border-b">{t('purpose.row_1_col_2')}</td>
                                <td className="px-4 py-2 border-b">{t('purpose.row_1_col_3')}</td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 border-b">{t('purpose.row_2_col_1')}</td>
                                <td className="px-4 py-2 border-b">{t('purpose.row_2_col_2')}</td>
                                <td className="px-4 py-2 border-b">{t('purpose.row_2_col_3')}</td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 border-b">{t('purpose.row_3_col_1')}</td>
                                <td className="px-4 py-2 border-b">{t('purpose.row_3_col_2')}</td>
                                <td className="px-4 py-2 border-b">{t('purpose.row_3_col_3')}</td>
                            </tr>
                            <tr>
                                <td className="px-4 py-2 border-b">{t('purpose.row_4_col_1')}</td>
                                <td className="px-4 py-2 border-b">{t('purpose.row_4_col_2')}</td>
                                <td className="px-4 py-2 border-b">{t('purpose.row_4_col_3')}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">4. {t('public_data.title')}</h2>
                <p className="whitespace-pre-line">{t('public_data.desc')}</p>
            </section>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">5. {t('cookies.title')}</h2>
                <p className="mb-4">{t('cookies.intro')}</p>

                <h3 className="text-xl font-medium mb-2">{t('cookies.necessary_title')}</h3>
                <ul className="list-disc pl-5 mb-4 space-y-1">
                    <li dangerouslySetInnerHTML={{ __html: t.raw('cookies.necessary_1') }} />
                    <li dangerouslySetInnerHTML={{ __html: t.raw('cookies.necessary_2') }} />
                    <li dangerouslySetInnerHTML={{ __html: t.raw('cookies.necessary_3') }} />
                </ul>

                <h3 className="text-xl font-medium mb-2">{t('cookies.analytics_title')}</h3>
                <p className="mb-4">{t('cookies.analytics_1')}</p>
                <p>{t('cookies.analytics_2')}</p>
            </section>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">6. {t('data_sharing.title')}</h2>
                <p className="mb-2">{t('data_sharing.intro')}</p>
                <ul className="list-disc pl-5 space-y-1">
                    <li dangerouslySetInnerHTML={{ __html: t.raw('data_sharing.list_1') }} />
                    <li dangerouslySetInnerHTML={{ __html: t.raw('data_sharing.list_2') }} />
                    <li dangerouslySetInnerHTML={{ __html: t.raw('data_sharing.list_3') }} />
                </ul>
            </section>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">7. {t('data_retention.title')}</h2>
                <ul className="list-disc pl-5 space-y-1">
                    <li dangerouslySetInnerHTML={{ __html: t.raw('data_retention.list_1') }} />
                    <li dangerouslySetInnerHTML={{ __html: t.raw('data_retention.list_2') }} />
                </ul>
            </section>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">8. {t('your_rights.title')}</h2>
                <p className="mb-2">{t('your_rights.intro')}</p>
                <ul className="list-disc pl-5 mb-4 space-y-1">
                    <li>{t('your_rights.list_1')}</li>
                    <li>{t('your_rights.list_2')}</li>
                    <li>{t('your_rights.list_3')}</li>
                    <li>{t('your_rights.list_4')}</li>
                    <li>{t('your_rights.list_5')}</li>
                </ul>
                <p>{t('your_rights.outro')}</p>
            </section>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">9. {t('security.title')}</h2>
                <p className="mb-2">{t('security.intro')}</p>
                <ul className="list-disc pl-5 space-y-1">
                    <li>{t('security.list_1')}</li>
                    <li>{t('security.list_2')}</li>
                    <li>{t('security.list_3')}</li>
                </ul>
            </section>

            <section className="mb-8">
                <h2 className="text-2xl font-semibold mb-4">10. {t('changes.title')}</h2>
                <p>{t('changes.desc')}</p>
            </section>
        </div>
    );
}
