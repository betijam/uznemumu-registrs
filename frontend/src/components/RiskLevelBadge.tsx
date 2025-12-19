"use client";

interface RiskLevelBadgeProps {
    level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE';
    score: number;
    size?: 'sm' | 'md' | 'lg';
}

export default function RiskLevelBadge({ level, score, size = 'md' }: RiskLevelBadgeProps) {
    const getStyles = () => {
        switch (level) {
            case 'CRITICAL':
                return {
                    bg: 'bg-red-600',
                    text: 'text-white',
                    icon: '🔴',
                    label: 'KRITISKS'
                };
            case 'HIGH':
                return {
                    bg: 'bg-orange-500',
                    text: 'text-white',
                    icon: '🟠',
                    label: 'AUGSTS'
                };
            case 'MEDIUM':
                return {
                    bg: 'bg-yellow-500',
                    text: 'text-white',
                    icon: '🟡',
                    label: 'VIDĒJS'
                };
            case 'LOW':
                return {
                    bg: 'bg-blue-500',
                    text: 'text-white',
                    icon: '🔵',
                    label: 'ZEMS'
                };
            case 'NONE':
                return {
                    bg: 'bg-success',
                    text: 'text-white',
                    icon: '🟢',
                    label: 'NAV RISKU'
                };
        }
    };

    const styles = getStyles();

    const sizeClasses = {
        sm: 'text-xs px-2 py-1',
        md: 'text-sm px-3 py-1.5',
        lg: 'text-base px-4 py-2'
    };

    return (
        <div className={`inline-flex items-center gap-2 ${styles.bg} ${styles.text} ${sizeClasses[size]} rounded-full font-semibold`}>
            <span>{styles.icon}</span>
            <span>{styles.label}</span>
            <span className="opacity-75">({score})</span>
        </div>
    );
}
