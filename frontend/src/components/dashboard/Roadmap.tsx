"use client";

import { useTranslations } from "next-intl";

export default function Roadmap() {
    const t = useTranslations('Roadmap');

    const roadmapItems = [
        {
            status: "ready",
            icon: "✅",
            title: t('status_ready'),
            items: [t('ready_search'), t('ready_financials'), t('ready_top_lists')]
        },
        {
            status: "in_progress",
            icon: "🚧",
            title: t('status_in_progress'),
            items: [t('progress_export'), t('progress_history'), t('progress_map')]
        },
        {
            status: "planned",
            icon: "🚀",
            title: t('status_planned'),
            items: [t('planned_api'), t('planned_risk'), t('planned_monitoring')]
        }
    ];

    return (
        <section className="py-16 bg-white border-t border-gray-100">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-12">
                    <h2 className="text-3xl font-bold text-gray-900">{t('section_title')}</h2>
                    <p className="mt-4 text-lg text-gray-500 max-w-2xl mx-auto">
                        {t('section_subtitle')}
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {roadmapItems.map((item) => (
                        <div key={item.status} className="bg-gray-50 rounded-xl p-6 border border-gray-100 relative overflow-hidden">
                            <div className="flex items-center gap-3 mb-6">
                                <span className="text-2xl">{item.icon}</span>
                                <h3 className="text-xl font-bold text-gray-900">{item.title}</h3>
                            </div>

                            <ul className="space-y-3">
                                {item.items.map((subItem, idx) => (
                                    <li key={idx} className="flex items-start text-gray-600">
                                        <span className="mr-2 text-purple-600 font-bold">•</span>
                                        {subItem}
                                    </li>
                                ))}
                            </ul>

                            {item.status === 'planned' && (
                                <div className="absolute top-0 right-0 bg-purple-100 text-purple-700 text-xs font-bold px-2 py-1 rounded-bl-lg">
                                    PRO
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
