import { Link } from "@/i18n/routing";

export default function Footer() {
    return (
        <footer className="bg-white border-t border-gray-100 py-12 mt-auto">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
                    <div className="col-span-1 md:col-span-2">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">Company 360</h3>
                        <p className="text-gray-500 text-sm max-w-xs">
                            Moderns un ērts rīks Latvijas uzņēmumu datu analīzei.
                            Apvienojam publiski pieejamos datus vienuviet.
                        </p>
                    </div>
                    <div>
                        <h4 className="font-semibold text-gray-900 mb-4">Saites</h4>
                        <ul className="space-y-2 text-sm text-gray-600">
                            <li><Link href="/" className="hover:text-purple-600">Sākums</Link></li>
                            <li><Link href="/top100" className="hover:text-purple-600">TOP 100</Link></li>
                            <li><Link href="/industries" className="hover:text-purple-600">Nozares</Link></li>
                        </ul>
                    </div>
                    <div>
                        <h4 className="font-semibold text-gray-900 mb-4">Dati</h4>
                        <ul className="space-y-2 text-sm text-gray-600">
                            <li><a href="https://data.gov.lv" target="_blank" rel="noopener noreferrer" className="hover:text-purple-600">Latvijas Atvērtie Dati</a></li>
                        </ul>
                    </div>
                </div>
                <div className="border-t border-gray-100 pt-8 flex flex-col md:flex-row justify-between items-center text-xs text-gray-400">
                    <div className="flex flex-wrap justify-center md:justify-start items-center gap-1">
                        <span>&copy; {new Date().getFullYear()} Company 360.</span>
                        <span className="ml-1">Powered by</span>
                        <a href="https://animas.lv/" target="_blank" rel="noopener noreferrer" className="inline-flex items-center hover:opacity-80 transition-opacity">
                            <img src="/api/map/logo" alt="ANIMAS" width={263} height={28} className="h-4 w-auto mb-0.5" />
                        </a>
                        <span className="mx-1 text-gray-300">|</span>
                        <span>Visas tiesības aizsargātas.</span>
                    </div>
                    <p className="mt-2 md:mt-0">Dati tiek atjaunoti reizi dienā.</p>
                </div>
            </div>
        </footer>
    );
}
