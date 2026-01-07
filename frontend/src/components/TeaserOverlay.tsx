import { Link } from "@/i18n/routing";
import { useTranslations } from "next-intl";

export const TeaserOverlay = () => {
    const t = useTranslations('AccessControl');
    return (
        <div className="relative border border-gray-200 rounded-lg p-8 bg-gray-50 text-center overflow-hidden">
            {/* Blurred Background Mockup */}
            <div className="absolute inset-0 filter blur-md opacity-50 bg-white pointer-events-none select-none flex flex-col gap-4 p-8">
                <div className="h-4 bg-gray-300 rounded w-3/4 mx-auto"></div>
                <div className="h-4 bg-gray-300 rounded w-1/2 mx-auto"></div>
                <div className="h-32 bg-gray-200 rounded w-full"></div>
                <div className="grid grid-cols-3 gap-4">
                    <div className="h-10 bg-gray-200 rounded"></div>
                    <div className="h-10 bg-gray-200 rounded"></div>
                    <div className="h-10 bg-gray-200 rounded"></div>
                </div>
            </div>

            {/* Content */}
            <div className="relative z-10 max-w-md mx-auto py-8">
                <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{t('restricted_access')}</h3>
                <p className="text-gray-600 mb-6">{t('register_to_view_full')}</p>
                <div className="flex justify-center gap-3">
                    <Link href="/auth/register" className="px-6 py-2.5 bg-primary text-white font-medium rounded-lg hover:bg-primary-dark transition-colors shadow-sm">
                        {t('register_now')}
                    </Link>
                    <Link href="/auth/login" className="px-6 py-2.5 bg-white text-gray-700 font-medium rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors">
                        {t('login')}
                    </Link>
                </div>
                <p className="text-xs text-gray-500 mt-4">
                    {t('free_views_limit')}
                </p>
            </div>
        </div>
    );
};

export default TeaserOverlay;
