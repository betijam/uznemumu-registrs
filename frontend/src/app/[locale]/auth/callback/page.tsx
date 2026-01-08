"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Cookies from "js-cookie";

function CallbackContent() {
    const router = useRouter();
    const searchParams = useSearchParams();

    useEffect(() => {
        const token = searchParams.get("token");
        if (token) {
            // Set token in cookie (valid for 30 days matches backend)
            Cookies.set("token", token, { expires: 30 });
            // Force refresh to update auth state context if using one, or just redundant safety
            router.refresh();
            router.push("/");
        } else {
            // If no token, redirect to login
            router.push("/auth/login?error=auth_failed");
        }
    }, [searchParams, router]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="text-center">
                <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <h2 className="text-xl font-semibold text-gray-900">Pieslēdzas...</h2>
                <p className="text-gray-500">Lūdzu uzgaidiet, kamēr mēs apstrādājam jūsu piekļuvi.</p>
            </div>
        </div>
    );
}

export default function AuthCallbackPage() {
    return (
        <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Loading...</div>}>
            <CallbackContent />
        </Suspense>
    );
}
