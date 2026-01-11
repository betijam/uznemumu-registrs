"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/routing";
import { useState } from "react";
import Navbar from "@/components/Navbar";

export default function PricingPage() {
    const t = useTranslations('Pricing');
    const [email, setEmail] = useState("");
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email) return;

        setStatus('loading');
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/waitlist/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, source: 'pricing_page' }),
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

    return (
        <div className="bg-gray-50 min-h-screen">
            <Navbar />

            {/* Hero Section */}
            <div className="bg-white border-b border-gray-200 pt-16 pb-24 px-4 sm:px-6 lg:px-8 text-center">
                <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl">
                    <span className="block">{t('title')}</span>
                </h1>
                <p className="mt-5 max-w-xl mx-auto text-xl text-gray-500">
                    {t('subtitle')}
                </p>
            </div>

            {/* Pricing Cards */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-12 relative z-10 pb-20">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">

                    {/* Basic Plan */}
                    <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden flex flex-col">
                        <div className="p-8 flex-1">
                            <h3 className="text-xl font-semibold text-gray-900">{t('basic_plan')}</h3>
                            <p className="mt-4 flex items-baseline text-gray-900">
                                <span className="text-5xl font-extrabold tracking-tight">€0</span>
                                <span className="ml-1 text-xl font-semibold text-gray-500">/{t('month')}</span>
                            </p>
                            <p className="mt-6 text-gray-500">{t('basic_desc')}</p>

                            <ul role="list" className="mt-6 space-y-6">
                                {[
                                    t('feature_search'),
                                    t('feature_top_lists'),
                                    t('feature_basic_profile'),
                                    t('feature_map')
                                ].map((feature) => (
                                    <li key={feature} className="flex">
                                        <svg className="flex-shrink-0 w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                        <span className="ml-3 text-gray-500">{feature}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                        <div className="p-8 bg-gray-50 border-t border-gray-100">
                            <Link
                                href="/"
                                className="block w-full bg-white border border-gray-300 rounded-md py-3 text-sm font-semibold text-gray-700 text-center hover:bg-gray-50 transition-colors"
                            >
                                {t('start_free')}
                            </Link>
                        </div>
                    </div>

                    {/* Pro Plan */}
                    <div className="bg-white rounded-2xl shadow-xl border-2 border-purple-600 overflow-hidden flex flex-col relative">
                        <div className="absolute top-0 right-0 bg-purple-600 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
                            {t('coming_soon')}
                        </div>
                        <div className="p-8 flex-1">
                            <h3 className="text-xl font-semibold text-gray-900">{t('pro_plan')}</h3>
                            <p className="mt-4 flex items-baseline text-gray-900">
                                <span className="text-2xl font-bold tracking-tight">{t('early_access')}</span>
                            </p>
                            <p className="mt-6 text-gray-500">{t('pro_desc')}</p>

                            <ul role="list" className="mt-6 space-y-6">
                                {[
                                    t('feature_history'),
                                    t('feature_export'),
                                    t('feature_monitoring'),
                                    t('feature_b2b_contacts')
                                ].map((feature) => (
                                    <li key={feature} className="flex">
                                        <div className="bg-purple-100 rounded-full p-1">
                                            <svg className="flex-shrink-0 w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                            </svg>
                                        </div>
                                        <span className="ml-3 text-gray-900 font-medium">{feature}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                        <div className="p-8 bg-purple-50 border-t border-purple-100">
                            {status === 'success' ? (
                                <div className="text-center p-2 bg-green-100 text-green-700 rounded-lg border border-green-200">
                                    <p className="font-semibold">✓ {t('waitlist_joined')}</p>
                                    <p className="text-sm mt-1">{t('waitlist_thank_you')}</p>
                                </div>
                            ) : (
                                <form onSubmit={handleSubmit} className="mt-2">
                                    <label htmlFor="email" className="sr-only">Email address</label>
                                    <div className="flex gap-2">
                                        <input
                                            type="email"
                                            name="email"
                                            id="email"
                                            required
                                            className="flex-1 min-w-0 px-4 py-2 text-base text-gray-900 placeholder-gray-500 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                                            placeholder={t('email_placeholder')}
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            disabled={status === 'loading'}
                                        />
                                        <button
                                            type="submit"
                                            disabled={status === 'loading'}
                                            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 transition-colors"
                                        >
                                            {status === 'loading' ? '...' : t('join_waitlist')}
                                        </button>
                                    </div>
                                    {status === 'error' && (
                                        <p className="text-red-600 text-sm mt-2 text-center">{t('error_msg')}</p>
                                    )}
                                    <p className="mt-3 text-xs text-center text-gray-500">
                                        {t('no_spam_promise')}
                                    </p>
                                </form>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
