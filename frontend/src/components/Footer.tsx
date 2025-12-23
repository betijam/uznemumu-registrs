import Link from "next/link";

export default function Footer() {
    return (
        <footer className="bg-white border-t border-gray-100 py-12 mt-auto">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
                    <div className="col-span-1 md:col-span-2">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">Latvijas Uzņēmumu Reģistrs 2.0</h3>
                        <p className="text-gray-500 text-sm max-w-xs">
                            Moderns un ērts rīks Latvijas uzņēmumu datu analīzei.
                            Apvienojam publiski pieejamos datus vienuviet.
                        </p>
                    </div>
                    <div>
                        <h4 className="font-semibold text-gray-900 mb-4">Saites</h4>
                        <ul className="space-y-2 text-sm text-gray-600">
                            <li><Link href="/" className="hover:text-purple-600">Sākums</Link></li>
                            <li><Link href="/top-100" className="hover:text-purple-600">TOP 100</Link></li>
                            <li><Link href="/industries" className="hover:text-purple-600">Nozares</Link></li>
                            <li><Link href="/about" className="hover:text-purple-600">Par Mums</Link></li>
                        </ul>
                    </div>
                    <div>
                        <h4 className="font-semibold text-gray-900 mb-4">Dati</h4>
                        <ul className="space-y-2 text-sm text-gray-600">
                            <li><a href="https://info.ur.gov.lv" target="_blank" rel="noopener noreferrer" className="hover:text-purple-600">UR Atvērtie Dati</a></li>
                            <li><a href="https://data.gov.lv" target="_blank" rel="noopener noreferrer" className="hover:text-purple-600">Latvijas Atvērtie Dati</a></li>
                        </ul>
                    </div>
                </div>
                <div className="border-t border-gray-100 pt-8 flex flex-col md:flex-row justify-between items-center text-xs text-gray-400">
                    <p>&copy; {new Date().getFullYear()} Latvijas Uzņēmumu Reģistrs 2.0. Visas tiesības aizsargātas.</p>
                    <p className="mt-2 md:mt-0">Dati tiek atjaunoti reizi dienā.</p>
                </div>
            </div>
        </footer>
    );
}
