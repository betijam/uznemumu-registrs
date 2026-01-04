import { useTranslations } from 'next-intl';

interface CompanySizeBadgeProps {
    size: string | null;
}

export default function CompanySizeBadge({ size }: CompanySizeBadgeProps) {
    const t = useTranslations('CompanySize');

    if (!size) return null;

    const sizeMap: Record<string, string> = {
        'Mikro': 'micro',
        'Mazs': 'small',
        'Vidējs': 'medium',
        'Liels': 'large'
    };

    const translationKey = sizeMap[size];
    if (!translationKey) return null;

    const badgeClasses: Record<string, string> = {
        'Mikro': 'bg-gray-100 text-gray-700 border-gray-300',
        'Mazs': 'bg-blue-100 text-blue-700 border-blue-300',
        'Vidējs': 'bg-purple-100 text-purple-700 border-purple-300',
        'Liels': 'bg-green-100 text-green-700 border-green-300'
    };

    return (
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${badgeClasses[size]}`}>
            {t(translationKey)}
        </span>
    );
}
