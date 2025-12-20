'use client';

interface LoadingSpinnerProps {
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

export default function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
    const sizeClasses = {
        sm: 'h-4 w-4',
        md: 'h-8 w-8',
        lg: 'h-12 w-12'
    };

    return (
        <div className={`flex items-center justify-center ${className}`}>
            <div className={`${sizeClasses[size]} border-4 border-primary border-t-transparent rounded-full animate-spin`} />
        </div>
    );
}

export function PageLoader() {
    return (
        <div className="flex items-center justify-center min-h-screen">
            <div className="text-center">
                <LoadingSpinner size="lg" className="mb-4" />
                <p className="text-gray-500">Ielādē datus...</p>
            </div>
        </div>
    );
}

export function SkeletonCard() {
    return (
        <div className="bg-white rounded-xl shadow-card p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-8 bg-gray-300 rounded w-1/2 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-2/3"></div>
        </div>
    );
}
