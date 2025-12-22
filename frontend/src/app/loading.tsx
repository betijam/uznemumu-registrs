export default function HomeLoading() {
    return (
        <main className="min-h-screen bg-gray-50">
            {/* Navbar skeleton */}
            <div className="bg-primary h-16"></div>

            {/* Hero Section - shows immediately */}
            <div className="relative bg-gradient-to-br from-primary via-primary to-accent overflow-hidden">
                <div className="relative z-10 pt-24 pb-32">
                    <div className="text-center">
                        <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-white mb-6">
                            Latvijas Uzņēmumu Reģistrs un<br />Analītika
                        </h1>
                        <p className="text-lg sm:text-xl text-gray-300 mb-10 max-w-3xl mx-auto">
                            Ātra, uzticama un detalizēta informācija par vairāk nekā 200,000 Latvijas uzņēmumiem.
                        </p>

                        {/* Search Bar skeleton */}
                        <div className="max-w-3xl mx-auto mb-8 px-4">
                            <div className="h-14 bg-white/20 rounded-xl animate-pulse"></div>
                        </div>

                        {/* Tags skeleton */}
                        <div className="flex flex-wrap justify-center gap-2 mb-4 px-4">
                            {[1, 2, 3, 4, 5].map((i) => (
                                <div key={i} className="h-8 w-24 bg-white/10 rounded-full animate-pulse"></div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Stats Cards skeleton */}
            <div className="max-w-6xl mx-auto px-4 -mt-16 relative z-20">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="bg-white rounded-xl shadow-lg p-6">
                            <div className="flex items-center gap-3 mb-3">
                                <div className="h-10 w-10 bg-gray-200 rounded-lg animate-pulse"></div>
                                <div className="h-4 w-32 bg-gray-200 rounded animate-pulse"></div>
                            </div>
                            <div className="h-8 w-24 bg-gray-200 rounded animate-pulse mb-2"></div>
                            <div className="h-3 w-40 bg-gray-200 rounded animate-pulse"></div>
                        </div>
                    ))}
                </div>
            </div>
        </main>
    );
}
