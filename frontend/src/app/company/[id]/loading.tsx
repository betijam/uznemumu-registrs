export default function CompanyLoading() {
    return (
        <div className="min-h-screen bg-gray-50 pb-12">
            {/* Navbar skeleton */}
            <div className="bg-primary h-16"></div>

            {/* Header skeleton */}
            <div className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    {/* Search bar placeholder */}
                    <div className="mb-4 max-w-md">
                        <div className="h-10 bg-gray-200 rounded-lg animate-pulse"></div>
                    </div>

                    <div className="flex items-start justify-between">
                        <div className="flex-1">
                            {/* Badges skeleton */}
                            <div className="flex items-center gap-2 mb-3">
                                <div className="h-6 w-16 bg-gray-200 rounded-full animate-pulse"></div>
                                <div className="h-6 w-24 bg-gray-200 rounded-full animate-pulse"></div>
                                <div className="h-6 w-20 bg-gray-200 rounded-full animate-pulse"></div>
                            </div>

                            {/* Company name skeleton */}
                            <div className="h-9 w-80 bg-gray-200 rounded-lg animate-pulse mb-3"></div>

                            {/* Address skeleton */}
                            <div className="flex items-center gap-4">
                                <div className="h-5 w-40 bg-gray-200 rounded animate-pulse"></div>
                                <div className="h-5 w-60 bg-gray-200 rounded animate-pulse"></div>
                            </div>
                        </div>

                        {/* Button skeleton */}
                        <div className="h-10 w-32 bg-gray-200 rounded-lg animate-pulse"></div>
                    </div>
                </div>
            </div>

            {/* Metric Cards skeleton */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 mb-8 relative z-10">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="bg-white rounded-xl shadow-md p-5">
                            <div className="flex items-center justify-between mb-2">
                                <div className="h-4 w-24 bg-gray-200 rounded animate-pulse"></div>
                                <div className="h-5 w-5 bg-gray-200 rounded animate-pulse"></div>
                            </div>
                            <div className="h-8 w-28 bg-gray-200 rounded animate-pulse mb-2"></div>
                            <div className="h-3 w-16 bg-gray-200 rounded animate-pulse"></div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Content skeleton */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                    {/* Left card */}
                    <div className="bg-white rounded-xl shadow-md p-6">
                        <div className="h-6 w-40 bg-gray-200 rounded animate-pulse mb-4"></div>
                        <div className="space-y-3">
                            <div className="h-4 w-full bg-gray-200 rounded animate-pulse"></div>
                            <div className="h-4 w-3/4 bg-gray-200 rounded animate-pulse"></div>
                        </div>
                    </div>

                    {/* Right card */}
                    <div className="bg-white rounded-xl shadow-md p-6">
                        <div className="h-6 w-40 bg-gray-200 rounded animate-pulse mb-4"></div>
                        <div className="space-y-3">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse"></div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
