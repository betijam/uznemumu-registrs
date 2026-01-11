"use client";

import { useTranslations } from "next-intl";
import { useState, Fragment } from "react";
import { Dialog, Transition } from "@headlessui/react";
import { Link } from "@/i18n/routing";

interface WaitlistModalProps {
    isOpen: boolean;
    onClose: () => void;
    featureName?: string;
}

export default function WaitlistModal({ isOpen, onClose, featureName }: WaitlistModalProps) {
    const t = useTranslations('ProFeature');
    const [email, setEmail] = useState("");
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email) return;

        setStatus('loading');
        try {
            const response = await fetch('/api/waitlist/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, source: `feature_lock_${featureName || 'unknown'}` }),
            });

            if (response.ok) {
                setStatus('success');
                setEmail("");
            } else {
                setStatus('error');
            }
        } catch (error) {
            console.error(error);
            setStatus('error');
        }
    };

    return (
        <Transition appear show={isOpen} as={Fragment}>
            <Dialog className="relative z-50" onClose={onClose}>
                <Transition.Child
                    as={Fragment}
                    enter="ease-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-200"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-black bg-opacity-25" />
                </Transition.Child>

                <div className="fixed inset-0 overflow-y-auto">
                    <div className="flex min-h-full items-center justify-center p-4 text-center">
                        <Transition.Child
                            as={Fragment}
                            enter="ease-out duration-300"
                            enterFrom="opacity-0 scale-95"
                            enterTo="opacity-100 scale-100"
                            leave="ease-in duration-200"
                            leaveFrom="opacity-100 scale-100"
                            leaveTo="opacity-0 scale-95"
                        >
                            <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                                <button
                                    onClick={onClose}
                                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-500"
                                >
                                    <span className="sr-only">Close</span>
                                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>

                                <div className="text-center">
                                    <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-purple-100 mb-4">
                                        <svg className="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                        </svg>
                                    </div>
                                    <Dialog.Title className="text-lg font-medium leading-6 text-gray-900">
                                        {t('modal_title')}
                                    </Dialog.Title>
                                    <div className="mt-2 text-sm text-gray-500">
                                        <p className="mb-4">
                                            {t('modal_desc', { feature: featureName || '' })}
                                        </p>
                                        <p className="font-semibold text-purple-700">
                                            {t('modal_cta')}
                                        </p>
                                    </div>

                                    {status === 'success' ? (
                                        <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-100 text-green-700">
                                            <p className="font-semibold text-sm">✓ {t('success_title')}</p>
                                            <p className="text-xs mt-1">{t('success_desc')}</p>
                                            <button
                                                onClick={onClose}
                                                className="mt-3 text-sm font-medium underline hover:text-green-800"
                                            >
                                                {t('close')}
                                            </button>
                                        </div>
                                    ) : (
                                        <form onSubmit={handleSubmit} className="mt-6">
                                            <div>
                                                <label htmlFor="modal-email" className="sr-only">Email</label>
                                                <input
                                                    type="email"
                                                    id="modal-email"
                                                    required
                                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                                                    placeholder={t('email_placeholder')}
                                                    value={email || ""}
                                                    onChange={(e) => setEmail(e.target.value)}
                                                    disabled={status === 'loading'}
                                                />
                                            </div>
                                            <button
                                                type="submit"
                                                disabled={status === 'loading'}
                                                className="w-full mt-3 px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:opacity-50"
                                            >
                                                {status === 'loading' ? '...' : t('join_button')}
                                            </button>
                                            {status === 'error' && (
                                                <p className="mt-2 text-xs text-red-600">{t('error_msg')}</p>
                                            )}
                                            <p className="mt-3 text-xs text-gray-400">
                                                {t('privacy_note')}
                                            </p>
                                        </form>
                                    )}
                                </div>
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
}
