"use client";

import { useState } from "react";
import WaitlistModal from "./WaitlistModal";

interface ProFeatureButtonProps {
    children: React.ReactNode;
    featureName: string;
    className?: string; // To allow applying classes to the wrapper div or button
    asChild?: boolean; // If true, clones the child application logic (advanced), for now let's just wrap
}

export default function ProFeatureButton({ children, featureName, className }: ProFeatureButtonProps) {
    const [isOpen, setIsOpen] = useState(false);

    // We intercept the click.
    // Ideally this component wraps the button or is the button itself.
    // Let's make it a wrapper that captures click events.

    return (
        <>
            <div
                className={`relative inline-block cursor-pointer group ${className || ''}`}
                onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setIsOpen(true);
                }}
            >
                {/* Overlay lock icon on hover or always? Let's do on hover or a small badge */}
                <div className="absolute -top-2 -right-2 z-10 bg-purple-600 text-white rounded-full p-1 shadow-md scale-0 group-hover:scale-100 transition-transform duration-200">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                </div>

                {children}
            </div>

            <WaitlistModal
                isOpen={isOpen}
                onClose={() => setIsOpen(false)}
                featureName={featureName}
            />
        </>
    );
}
