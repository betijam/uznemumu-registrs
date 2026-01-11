import { Link } from "@/i18n/routing";
import { useTranslations } from "next-intl";

export default function Footer() {
    const t = useTranslations('Footer');
    const nav = useTranslations('Navigation');

    return (
        <footer className="bg-slate-900 text-white py-12 mt-auto">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
                    {/* Column 1: Brand */}
                    <div className="col-span-1">
                        <div className="flex items-center gap-2 mb-4">
                            <img
                                src="/company360.png"
                                alt="Company 360"
                                className="h-8 w-auto brightness-0 invert"
                            />
                        </div>
                        <p className="text-gray-400 text-sm max-w-xs leading-relaxed">
                            {t('description')}
                        </p>
                    </div>

                    {/* Column 2: Product */}
                    <div>
                        <h4 className="font-semibold text-white mb-4">{t('product_title')}</h4>
                        <ul className="space-y-3 text-sm text-gray-400">
                            <li><Link href="/" className="hover:text-white transition-colors">{nav('home')}</Link></li>
                            <li><Link href="/pricing" className="hover:text-white transition-colors">{nav('pricing')}</Link></li>
                            <li><Link href="/explore" className="hover:text-white transition-colors">{nav('analytics')}</Link></li>
                        </ul>
                    </div>

                    {/* Column 3: Legal */}
                    <div>
                        <h4 className="font-semibold text-white mb-4">{t('legal_title')}</h4>
                        <ul className="space-y-3 text-sm text-gray-400">
                            <li><Link href="/privacy" className="hover:text-white transition-colors">{t('privacy_policy')}</Link></li>
                            <li><Link href="/cookies" className="hover:text-white transition-colors">{t('cookie_policy')}</Link></li>
                        </ul>
                    </div>

                    {/* Column 4: Data */}
                    <div>
                        <h4 className="font-semibold text-white mb-4">{t('contacts_title')}</h4>
                        <ul className="space-y-3 text-sm text-gray-400">
                            <li className="flex items-center gap-2">
                                <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                                <a href="mailto:info@company360.lv" className="hover:text-white transition-colors">info@company360.lv</a>
                            </li>
                            <li>
                                <span className="text-gray-500 text-xs block mb-1">{t('data_source')}:</span>
                                <a href="https://data.gov.lv" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                                    {t('open_data')}
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>

                <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center text-xs text-gray-500">
                    <div className="flex flex-wrap justify-center md:justify-start items-center gap-2">
                        <span>&copy; {new Date().getFullYear()} Company 360.</span>
                        <span>{t('powered_by')}</span>
                        <a href="https://animas.lv/" target="_blank" rel="noopener noreferrer" className="inline-flex items-center hover:opacity-80 transition-opacity">
                            <img src="/api/map/logo" alt="ANIMAS" className="h-4 w-auto brightness-0 invert opacity-70" />
                        </a>
                    </div>
                    <p className="mt-2 md:mt-0 text-gray-500">{t('data_update')}</p>
                </div>
            </div>
        </footer>
    );
}
