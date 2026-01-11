import { Link } from "@/i18n/routing";
import { useTranslations } from "next-intl";

export default function Footer() {
    const t = useTranslations('Footer');
    const nav = useTranslations('Navigation');
    const home = useTranslations('HomePage');

    return (
        <footer className="bg-white border-t border-gray-100 py-12 mt-auto">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
                    <div className="col-span-1 md:col-span-2">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">Company 360</h3>
                        <p className="text-gray-500 text-sm max-w-xs">
                            {t('description')}
                        </p>
                    </div>
                    <div>
                        <h4 className="font-semibold text-gray-900 mb-4">{t('links_title')}</h4>
                        <ul className="space-y-2 text-sm text-gray-600">
                            <li><Link href="/" className="hover:text-purple-600">{nav('home')}</Link></li>
                            <li><Link href="/explore?sort_by=turnover&order=desc" className="hover:text-purple-600">{home('top100')}</Link></li>
                            <li><Link href="/industries" className="hover:text-purple-600">{nav('industries')}</Link></li>
                        </ul>
                    </div>
                    <div>
                        <h4 className="font-semibold text-gray-900 mb-4">{t('data_title')}</h4>
                        <ul className="space-y-2 text-sm text-gray-600">
                            <li><a href="https://data.gov.lv" target="_blank" rel="noopener noreferrer" className="hover:text-purple-600">{t('open_data')}</a></li>
                        </ul>
                    </div>
                </div>
                <div className="border-t border-gray-100 pt-8 flex flex-col md:flex-row justify-between items-center text-xs text-gray-400">
                    <div className="flex flex-wrap justify-center md:justify-start items-center gap-1">
                        <span>&copy; {new Date().getFullYear()} Company 360.</span>
                        <span className="ml-1">{t('powered_by')}</span>
                        <a href="https://animas.lv/" target="_blank" rel="noopener noreferrer" className="inline-flex items-center hover:opacity-80 transition-opacity">
                            <img src="/api/map/logo" alt="ANIMAS" width={263} height={28} className="h-4 w-auto mb-0.5" />
                        </a>
                        <span className="mx-1 text-gray-300">|</span>
                        <span>{t('rights_reserved')}</span>

                        <span className="mx-1 text-gray-300 hidden md:inline">|</span>
                        <div className="flex gap-4 mt-2 md:mt-0">
                            <Link href="/privacy" className="hover:text-purple-600 transition-colors">
                                {t('privacy_policy')}
                            </Link>
                            <Link href="/cookies" className="hover:text-purple-600 transition-colors">
                                {t('cookie_policy')}
                            </Link>
                        </div>
                    </div>
                    <p className="mt-2 md:mt-0">{t('data_update')}</p>
                </div>
            </div>
        </footer>
    );
}
