"use client";

import React from 'react';
import DataDiggingLoader from '@/components/DataDiggingLoader';

export default function LoaderTestPage() {
    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
            <h1 className="text-2xl font-bold mb-8 text-slate-800">Loader Animation Preview</h1>
            <div className="p-10 border border-gray-200 rounded-xl bg-white shadow-sm">
                <DataDiggingLoader />
            </div>
            <p className="mt-8 text-slate-500 max-w-md text-center">
                This is a preview of the "Data Digging" animation.
                The component is located at <code>src/components/DataDiggingLoader.tsx</code>
            </p>
        </div>
    );
}
