import Link from "next/link";

export default function Navbar() {
    return (
        <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex items-center">
                        <Link href="/" className="flex-shrink-0 flex items-center gap-2">
                            <div className="w-8 h-8 bg-gradient-to-br from-accent to-primary rounded-lg flex items-center justify-center">
                                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                                </svg>
                            </div>
                            <span className="text-xl font-bold text-primary">UR Portāls</span>
                        </Link>
                    </div>
                    <div className="flex items-center gap-4">
                        <Link
                            href="/"
                            className="text-gray-600 hover:text-primary transition-colors text-sm font-medium"
                        >
                            Sākums
                        </Link>
                        <Link
                            href="/mvk-declaration"
                            className="text-gray-600 hover:text-primary transition-colors text-sm font-medium"
                        >
                            MVK Deklarācija
                        </Link>
                        <button className="inline-flex items-center gap-2 px-4 py-2 border border-transparent rounded-lg text-sm font-medium text-white bg-primary hover:bg-secondary transition-colors shadow-sm">
                            Pieslēgties
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
}
