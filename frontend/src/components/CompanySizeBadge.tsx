'use client';

interface CompanySizeBadgeProps {
    size: string | null;
}

export default function CompanySizeBadge({ size }: CompanySizeBadgeProps) {
    if (!size) return null;

    const badgeConfig = {
        'Mikro': {
            label: 'MIKRO',
            className: 'bg-gray-100 text-gray-700 border-gray-300'
        },
        'Mazs': {
            label: 'MAZS UZŅĒMUMS',
            className: 'bg-blue-100 text-blue-700 border-blue-300'
        },
        'Vidējs': {
            label: 'VIDĒJS UZŅĒMUMS',
            className: 'bg-purple-100 text-purple-700 border-purple-300'
        },
        'Liels': {
            label: 'LIELS UZŅĒMUMS',
            className: 'bg-green-100 text-green-700 border-green-300'
        }
    };

    const config = badgeConfig[size as keyof typeof badgeConfig];
    if (!config) return null;

    return (
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${config.className}`}>
            {config.label}
        </span>
    );
}
