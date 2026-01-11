'use client';

import { useState, useEffect } from 'react';
import { Link } from '@/i18n/routing';

export default function CookieBanner() {
    const [showBanner, setShowBanner] = useState(false);

    useEffect(() => {
        // Check if user has already chosen
        const consent = localStorage.getItem('c360_cookie_consent');
        if (!consent) {
            // Small delay for better UX
            const timer = setTimeout(() => setShowBanner(true), 1000);
            return () => clearTimeout(timer);
        }
    }, []);

    const acceptAll = () => {
        localStorage.setItem('c360_cookie_consent', 'all');
        setShowBanner(false);
        // Here we would activate Google Analytics if we had it
        // window.gtag('consent', 'update', { ... });
    };

    const acceptNecessary = () => {
        localStorage.setItem('c360_cookie_consent', 'necessary');
        setShowBanner(false);
        // Do NOT activate Analytics here, but c360_free_views continues to work
        // as it is backend/middleware logic required for functionality.
    };

    if (!showBanner) return null;

    return (
        <div className="fixed bottom-0 left-0 right-0 z-50 p-4 md:p-6 bg-white border-t border-gray-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)] animate-slide-up">
            <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 md:gap-8">

                {/* Text part */}
                <div className="flex-1 text-sm text-gray-600">
                    <p className="font-semibold text-gray-900 mb-1">
                        🍪 Privātuma iestatījumi
                    </p>
                    <p>
                        Mēs izmantojam sīkdatnes, lai nodrošinātu portāla darbību (t.sk. bezmaksas piekļuves limitus) un analizētu plūsmu.
                        Nepieciešamās sīkdatnes ir obligātas pakalpojuma sniegšanai.
                        Vairāk informācijas <Link href="/privacy" className="text-primary hover:underline">Privātuma politikā</Link>.
                    </p>
                </div>

                {/* Buttons */}
                <div className="flex flex-col sm:flex-row gap-3 min-w-fit">
                    <button
                        onClick={acceptNecessary}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors whitespace-nowrap"
                    >
                        Tikai nepieciešamās
                    </button>
                    <button
                        onClick={acceptAll}
                        className="px-6 py-2 text-sm font-medium text-white bg-[#0f172a] hover:bg-[#1e293b] rounded-lg shadow-sm transition-transform active:scale-95 whitespace-nowrap"
                    >
                        Piekrītu visām
                    </button>
                </div>

            </div>
        </div>
    );
}
