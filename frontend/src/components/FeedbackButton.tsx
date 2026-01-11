"use client";

import { useState, Fragment } from "react";
import { Dialog, Transition } from "@headlessui/react";

export default function FeedbackButton() {
    const [isOpen, setIsOpen] = useState(false);
    const [feedback, setFeedback] = useState("");
    const [email, setEmail] = useState("");
    const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!feedback) return;

        setStatus('loading');
        try {
            const response = await fetch('/api/waitlist/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    feedback_text: feedback,
                    email: email || null,
                    source: 'feedback_button'
                }),
            });

            if (response.ok) {
                setStatus('success');
                setFeedback("");
                setEmail("");
            } else {
                setStatus('error');
            }
        } catch (error) {
            console.error(error);
            setStatus('error');
        }
    };

    const closeModal = () => {
        setIsOpen(false);
        setTimeout(() => {
            setStatus('idle');
            setFeedback("");
            setEmail("");
        }, 300);
    };

    return (
        <>
            {/* Floating Button */}
            <button
                onClick={() => setIsOpen(true)}
                className="fixed right-0 top-1/2 -translate-y-1/2 z-40 bg-white border border-gray-200 shadow-[0_4px_20px_rgba(0,0,0,0.1)] py-3 px-2 rounded-l-xl flex flex-col items-center gap-2 transition-transform hover:-translate-x-1 cursor-pointer group"
                title="Iesniegt ideju"
            >
                <div className="bg-yellow-100 text-yellow-600 p-2 rounded-full group-hover:scale-110 transition-transform">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                </div>
                <span className="text-xs font-bold text-slate-600 uppercase tracking-widest [writing-mode:vertical-rl] rotate-180">
                    Ieteikt ideju
                </span>
            </button>

            {/* Modal */}
            <Transition appear show={isOpen} as={Fragment}>
                <Dialog as="div" className="relative z-50" onClose={closeModal}>
                    <Transition.Child
                        as={Fragment}
                        enter="ease-out duration-300"
                        enterFrom="opacity-0"
                        enterTo="opacity-100"
                        leave="ease-in duration-200"
                        leaveFrom="opacity-100"
                        leaveTo="opacity-0"
                    >
                        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm" />
                    </Transition.Child>

                    <div className="fixed inset-0 overflow-y-auto">
                        <div className="flex min-h-full items-center justify-center p-4">
                            <Transition.Child
                                as={Fragment}
                                enter="ease-out duration-300"
                                enterFrom="opacity-0 scale-95"
                                enterTo="opacity-100 scale-100"
                                leave="ease-in duration-200"
                                leaveFrom="opacity-100 scale-100"
                                leaveTo="opacity-0 scale-95"
                            >
                                <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white shadow-2xl transition-all">
                                    {/* Header */}
                                    <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6 text-white relative">
                                        <button
                                            onClick={closeModal}
                                            className="absolute top-4 right-4 text-white/70 hover:text-white transition-colors"
                                        >
                                            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                            </svg>
                                        </button>
                                        <h3 className="text-xl font-bold mb-1">Tava ideja, mūsu plāns! 🚀</h3>
                                        <p className="text-indigo-100 text-sm">Kas pietrūkst Company 360? Mēs lasām visu.</p>
                                    </div>

                                    {/* Content */}
                                    <div className="p-6">
                                        {status === 'success' ? (
                                            <div className="text-center py-8">
                                                <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4 animate-bounce">
                                                    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                    </svg>
                                                </div>
                                                <h4 className="text-xl font-bold text-slate-900 mb-2">Paldies par ideju!</h4>
                                                <p className="text-slate-600 text-sm">Mēs to izskatīsim un, ja ieviesīsim, padosim ziņu.</p>
                                                <button
                                                    onClick={closeModal}
                                                    className="mt-6 text-indigo-600 font-medium hover:underline"
                                                >
                                                    Aizvērt logu
                                                </button>
                                            </div>
                                        ) : (
                                            <form onSubmit={handleSubmit}>
                                                <div className="mb-4">
                                                    <label className="block text-xs font-bold text-slate-700 uppercase mb-2">
                                                        Kas pietrūkst vai nestrādā?
                                                    </label>
                                                    <textarea
                                                        required
                                                        className="w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 text-slate-900 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none h-28 placeholder:text-gray-400"
                                                        placeholder="Piemēram: Gribētu redzēt vēsturiskos PLG datus vai eksportēt sarakstu uz Excel..."
                                                        value={feedback}
                                                        onChange={(e) => setFeedback(e.target.value)}
                                                        disabled={status === 'loading'}
                                                    />
                                                </div>

                                                <div className="mb-6">
                                                    <label className="block text-xs font-bold text-slate-700 uppercase mb-2">
                                                        Tavs E-pasts (ja vēlies atbildi)
                                                    </label>
                                                    <input
                                                        type="email"
                                                        className="w-full px-4 py-2 rounded-lg bg-gray-50 border border-gray-200 text-slate-900 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                                                        placeholder="vards@uznemums.lv"
                                                        value={email}
                                                        onChange={(e) => setEmail(e.target.value)}
                                                        disabled={status === 'loading'}
                                                    />
                                                </div>

                                                <button
                                                    type="submit"
                                                    disabled={status === 'loading'}
                                                    className="w-full py-3 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-lg transition-all shadow-lg transform hover:-translate-y-0.5 flex justify-center items-center gap-2 disabled:opacity-50"
                                                >
                                                    {status === 'loading' ? (
                                                        <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                        </svg>
                                                    ) : (
                                                        <>
                                                            <span>Nosūtīt ieteikumu</span>
                                                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                                                            </svg>
                                                        </>
                                                    )}
                                                </button>

                                                {status === 'error' && (
                                                    <p className="mt-2 text-sm text-red-600 text-center">Kļūda. Mēģiniet vēlāk.</p>
                                                )}
                                            </form>
                                        )}
                                    </div>
                                </Dialog.Panel>
                            </Transition.Child>
                        </div>
                    </div>
                </Dialog>
            </Transition>
        </>
    );
}
