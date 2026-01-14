"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";

export default function Roadmap() {
    const t = useTranslations('Roadmap');
    const [email, setEmail] = useState("");
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email) return;

        setStatus('loading');
        try {
            const response = await fetch('/api/waitlist/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, source: 'roadmap_newsletter' }),
            });

            if (response.ok) {
                setStatus('success');
                setEmail("");
            } else {
                setStatus('error');
            }
        } catch (error) {
            console.error(error);
            setStatus('error');
        }
    };

    const roadmapItems = [
        {
            status: "ready",
            icon: "✅",
            title: t('status_ready'),
            items: [
                t('ready_search'),
                t('ready_analytics'),
                t('ready_related'),
                t('ready_competitors')
            ]
        },
        {
            status: "in_progress",
            icon: "🚧",
            title: t('status_in_progress'),
            items: [
                t('progress_history'),
                t('progress_archive'),
                t('progress_mvk')
            ]
        },
        {
            status: "planned",
            icon: "🚀",
            title: t('status_planned'),
            items: [
                t('planned_ai'),
                t('planned_monitoring'),
                t('planned_reputation')
            ]
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

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
                    {roadmapItems.map((item) => (
                        <div key={item.status} className="bg-gray-50 rounded-xl p-6 border border-gray-100 relative overflow-hidden hover:shadow-md transition-shadow">
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

                {/* Newsletter CTA */}
                <div className="bg-slate-900 rounded-2xl p-8 md:p-12 text-center text-white relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-purple-600 rounded-full blur-3xl opacity-20 -mr-32 -mt-32"></div>

                    <div className="relative z-10">
                        <h3 className="text-2xl md:text-3xl font-bold mb-4">
                            {t('newsletter_title')}
                        </h3>
                        <p className="text-slate-300 mb-8 max-w-2xl mx-auto">
                            {t('newsletter_subtitle')}
                        </p>

                        {status === 'success' ? (
                            <div className="bg-green-500/20 border border-green-500/30 rounded-lg p-4 max-w-md mx-auto">
                                <p className="text-green-300 font-semibold">{t('newsletter_success')}</p>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
                                <input
                                    type="email"
                                    required
                                    className="flex-1 px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder={t('newsletter_placeholder')}
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    disabled={status === 'loading'}
                                />
                                <button
                                    type="submit"
                                    disabled={status === 'loading'}
                                    className="px-6 py-3 bg-white text-slate-900 rounded-lg font-semibold hover:bg-gray-100 transition-colors disabled:opacity-50"
                                >
                                    {status === 'loading' ? '...' : t('newsletter_button')}
                                </button>
                            </form>
                        )}
                        {status === 'error' && (
                            <p className="mt-2 text-sm text-red-400">{t('newsletter_error')}</p>
                        )}
                    </div>
                </div>
            </div>
        </section>
    );
}
