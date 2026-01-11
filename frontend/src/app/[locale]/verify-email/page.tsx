"use client";

import { useTranslations } from "next-intl";
import { useSearchParams, useRouter } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { Link } from "@/i18n/routing";

function VerifyEmailContent() {
    const t = useTranslations("Auth");
    const searchParams = useSearchParams();
    const token = searchParams.get("token");
    const router = useRouter();
    // Use lazy initialization to set initial status based on token presence
    const [status, setStatus] = useState<"loading" | "success" | "error">(() => {
        return token ? "loading" : "error";
    });

    useEffect(() => {
        if (!token) {
            return; // Status already set to "error" via lazy initialization
        }

        const verify = async () => {
            try {
                const res = await fetch(`/api/auth/verify-email?token=${token}`, {
                    method: "GET", // Or POST depending on backend
                });

                if (res.ok) {
                    setStatus("success");
                    // Redirect to login after a delay
                    setTimeout(() => {
                        router.push("/auth/login");
                    }, 3000);
                } else {
                    setStatus("error");
                }
            } catch {
                setStatus("error");
            }
        };

        verify();
    }, [token, router]);

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <div className="flex justify-center mb-6">
                    <Link href="/">
                        <img className="h-12 w-auto" src="/company360.png" alt="Company 360" />
                    </Link>
                </div>
                <h2 className="text-center text-3xl font-extrabold text-gray-900">
                    {t('email_verification')}
                </h2>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10 text-center">
                    {status === "loading" && (
                        <div className="flex flex-col items-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
                            <p className="text-gray-600">{t('verifying_email')}</p>
                        </div>
                    )}

                    {status === "success" && (
                        <div className="flex flex-col items-center">
                            <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center mb-4">
                                <span className="text-green-600 text-2xl">✓</span>
                            </div>
                            <p className="text-green-800 font-medium text-lg mb-2">{t('email_verified_success')}</p>
                            <p className="text-gray-500 text-sm mb-6">{t('redirecting_to_login')}</p>
                            <Link
                                href="/auth/login"
                                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                            >
                                {t('sign_in')}
                            </Link>
                        </div>
                    )}

                    {status === "error" && (
                        <div className="flex flex-col items-center">
                            <div className="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center mb-4">
                                <span className="text-red-600 text-2xl">✕</span>
                            </div>
                            <p className="text-red-800 font-medium text-lg mb-2">{t('email_verification_failed')}</p>
                            <p className="text-gray-500 text-sm mb-6">{t('verification_link_invalid')}</p>
                            <Link
                                href="/auth/login"
                                className="text-primary hover:text-primary/90 font-medium"
                            >
                                {t('back_to_login')}
                            </Link>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default function VerifyEmailPage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <VerifyEmailContent />
        </Suspense>
    );
}
