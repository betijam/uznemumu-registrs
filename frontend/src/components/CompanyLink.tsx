'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

interface CompanyLinkProps {
    regcode: number;
    children: React.ReactNode;
    className?: string;
}

export default function CompanyLink({ regcode, children, className = '' }: CompanyLinkProps) {
    const router = useRouter();
    const [isNavigating, setIsNavigating] = useState(false);

    const handleClick = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsNavigating(true);

        // Show loading indicator
        document.body.style.cursor = 'wait';

        // Navigate
        router.push(`/company/${regcode}`);
    };

    return (
        <a
            href={`/company/${regcode}`}
            onClick={handleClick}
            className={`${className} ${isNavigating ? 'opacity-50 pointer-events-none' : ''}`}
        >
            {isNavigating && (
                <span className="inline-block mr-2">
                    <svg className="animate-spin h-4 w-4 inline" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                </span>
            )}
            {children}
        </a>
    );
}
