"use client";

import { useState, useEffect } from "react";
import { Link } from "@/i18n/routing";
import { useTranslations } from 'next-intl';

interface TimelineEvent {
    date: string;
    year: number;
    type: 'active_role' | 'new_role' | 'exit' | 'liquidation';
    company_name: string;
    regcode: number;
    description: string;
    is_current: boolean;
}

interface CareerTimelineProps {
    person_id: string;
}

export default function CareerTimeline({ person_id }: CareerTimelineProps) {
    const t = useTranslations('CareerTimeline');
    const [events, setEvents] = useState<TimelineEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [hasMore, setHasMore] = useState(false);
    const [showAll, setShowAll] = useState(false);

    useEffect(() => {
        fetchTimeline();
    }, [person_id]);

    const fetchTimeline = async () => {
        setLoading(true);
        try {
            const limit = showAll ? 100 : 10;
            const res = await fetch(`/api/person/${person_id}/career-timeline?limit=${limit}`);
            const data = await res.json();
            setEvents(data.events || []);
            setHasMore(data.has_more);
        } catch (error) {
            console.error('Failed to fetch timeline:', error);
        }
        setLoading(false);
    };

    const getEventColor = (type: string) => {
        switch (type) {
            case 'active_role':
                return 'bg-blue-500';
            case 'new_role':
                return 'bg-green-500';
            case 'exit':
                return 'bg-red-500';
            case 'liquidation':
                return 'bg-gray-900';
            default:
                return 'bg-gray-400';
        }
    };

    const getEventIcon = (type: string) => {
        switch (type) {
            case 'active_role':
                return '●'; // Filled blue dot
            case 'new_role':
                return '●'; // Filled green dot
            case 'exit':
                return '✕'; // Red X
            case 'liquidation':
                return '⬛'; // Black square
            default:
                return '○'; // Hollow dot
        }
    };

    if (loading) {
        return (
            <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                <div className="animate-pulse space-y-4">
                    <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                    <div className="space-y-3">
                        <div className="h-12 bg-gray-200 rounded"></div>
                        <div className="h-12 bg-gray-200 rounded"></div>
                        <div className="h-12 bg-gray-200 rounded"></div>
                    </div>
                </div>
            </div>
        );
    }

    if (events.length === 0) {
        return (
            <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
                <h2 className="text-xl font-bold text-gray-800 mb-4">{t('title')}</h2>
                <p className="text-gray-500 text-center py-8">{t('no_data')}</p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
            <h2 className="text-xl font-bold text-gray-800 mb-6">{t('title')}</h2>

            {/* Timeline */}
            <div className="relative">
                {/* Vertical line */}
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />

                {/* Events */}
                <div className="space-y-6">
                    {events.map((event, idx) => (
                        <div key={idx} className="relative pl-12">
                            {/* Dot */}
                            <div className={`absolute left-0 w-8 h-8 rounded-full ${getEventColor(event.type)} flex items-center justify-center text-white font-bold text-lg shadow-md`}>
                                {getEventIcon(event.type)}
                            </div>

                            {/* Content */}
                            <div className="bg-gray-50 rounded-lg p-4 hover:shadow-md transition-shadow">
                                <div className="flex items-start justify-between gap-4">
                                    <div className="flex-1">
                                        <div className="text-sm text-gray-500 mb-1">{event.year}</div>
                                        <Link
                                            href={`/company/${event.regcode}`}
                                            className="text-lg font-semibold text-primary hover:underline"
                                        >
                                            {event.company_name}
                                        </Link>
                                        <div className="text-sm text-gray-700 mt-1">
                                            {t(event.type)}: {event.description}
                                        </div>
                                    </div>
                                    {event.is_current && (
                                        <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full whitespace-nowrap">
                                            {t('current')}
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Show more button */}
            {hasMore && !showAll && (
                <div className="mt-6 text-center">
                    <button
                        onClick={() => {
                            setShowAll(true);
                            fetchTimeline();
                        }}
                        className="px-6 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition-colors"
                    >
                        {t('show_more')}
                    </button>
                </div>
            )}
        </div>
    );
}
