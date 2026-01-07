'use client';

import { Link } from "@/i18n/routing";
import { useTranslations } from "next-intl";

export const TeaserOverlay = () => {
    const t = useTranslations('AccessControl');

    return (
        <div className="relative min-h-[450px] rounded-xl overflow-hidden bg-gradient-to-b from-gray-50 to-gray-100 border border-gray-200">

            {/* Blurred Background - Simulated Table/Data */}
            <div className="absolute inset-0 pointer-events-none select-none opacity-40">
                {/* Simulated table rows */}
                <div className="p-6 space-y-3">
                    <div className="flex gap-4">
                        <div className="h-4 bg-gray-300 rounded w-1/4 blur-[2px]"></div>
                        <div className="h-4 bg-gray-300 rounded w-1/3 blur-[2px]"></div>
                        <div className="h-4 bg-gray-200 rounded w-1/5 blur-[2px]"></div>
                    </div>
                    <div className="flex gap-4">
                        <div className="h-4 bg-gray-200 rounded w-1/3 blur-[2px]"></div>
                        <div className="h-4 bg-gray-300 rounded w-1/4 blur-[2px]"></div>
                        <div className="h-4 bg-gray-200 rounded w-1/4 blur-[2px]"></div>
                    </div>
                    <div className="h-24 bg-gray-200/50 rounded-lg blur-[3px] mt-4"></div>
                    <div className="flex gap-4">
                        <div className="h-4 bg-gray-300 rounded w-1/5 blur-[2px]"></div>
                        <div className="h-4 bg-gray-200 rounded w-2/5 blur-[2px]"></div>
                        <div className="h-4 bg-gray-300 rounded w-1/4 blur-[2px]"></div>
                    </div>
                    <div className="grid grid-cols-4 gap-3 mt-4">
                        <div className="h-10 bg-gray-200 rounded blur-[2px]"></div>
                        <div className="h-10 bg-gray-300 rounded blur-[2px]"></div>
                        <div className="h-10 bg-gray-200 rounded blur-[2px]"></div>
                        <div className="h-10 bg-gray-300 rounded blur-[2px]"></div>
                    </div>
                    <div className="flex gap-4">
                        <div className="h-4 bg-gray-300 rounded w-1/4 blur-[2px]"></div>
                        <div className="h-4 bg-gray-200 rounded w-1/3 blur-[2px]"></div>
                    </div>
                </div>
            </div>

            {/* Central Card */}
            <div className="relative z-10 flex items-center justify-center min-h-[450px] p-6">
                <div className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-xl p-8 max-w-md w-full border border-gray-100">

                    {/* Icon - Rocket (Positive) */}
                    <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-5 shadow-lg">
                        <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </div>

                    {/* Value Proposition Title */}
                    <h3 className="text-2xl font-bold text-gray-900 mb-2 text-center">
                        Atver pilnu finanšu analītiku
                    </h3>

                    {/* Explanation */}
                    <p className="text-gray-600 mb-6 text-center">
                        Dienas limits viesiem ir sasniegts.<br />
                        Reģistrējies, lai redzētu visus datus <span className="font-semibold text-green-600">bez maksas</span>.
                    </p>

                    {/* Benefits List */}
                    <div className="space-y-2 mb-6">
                        <div className="flex items-center gap-3 text-sm text-gray-700">
                            <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            <span>Vēsturiskie dati (5 gadi)</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm text-gray-700">
                            <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            <span>Amatpersonu vēsture</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm text-gray-700">
                            <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            <span>Nodokļu risku monitorings</span>
                        </div>
                    </div>

                    {/* Primary CTA - Register */}
                    <Link
                        href="/auth/register"
                        className="block w-full py-3.5 bg-gray-900 hover:bg-gray-800 text-white font-semibold rounded-xl text-center transition-all shadow-lg hover:shadow-xl"
                    >
                        Reģistrēties bez maksas
                    </Link>

                    {/* Secondary CTA - Login */}
                    <p className="text-center text-sm text-gray-500 mt-4">
                        Tev jau ir konts?{' '}
                        <Link href="/auth/login" className="text-indigo-600 hover:text-indigo-700 font-medium hover:underline">
                            Pieslēgties
                        </Link>
                    </p>

                    {/* Trust Signals */}
                    <div className="flex items-center justify-center gap-4 mt-6 pt-4 border-t border-gray-100">
                        <span className="text-xs text-gray-400 flex items-center gap-1">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                            </svg>
                            Nav kredītkartes
                        </span>
                        <span className="text-gray-300">•</span>
                        <span className="text-xs text-gray-400 flex items-center gap-1">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                            </svg>
                            Droši dati
                        </span>
                        <span className="text-gray-300">•</span>
                        <span className="text-xs text-gray-400 flex items-center gap-1">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            30 sekundes
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TeaserOverlay;
