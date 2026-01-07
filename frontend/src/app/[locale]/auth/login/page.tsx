"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Link, useRouter } from "@/i18n/routing";
import Cookies from "js-cookie";

export default function LoginPage() {
    const t = useTranslations('Auth');
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

            // NOTE: FormData is required by OAuth2PasswordRequestForm in FastAPI
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);

            const res = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                body: formData, // Automatic Content-Type: multipart/form-data
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || t('error_generic'));
            }

            const data = await res.json();
            // Store token in cookie
            Cookies.set('token', data.access_token, { expires: 30 }); // 30 days

            // Force refresh to update middleware/server-components
            router.refresh();
            router.push('/');
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-lg">
                <div>
                    <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                        {t('login_title')}
                    </h2>
                </div>
                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                    {error && (
                        <div className="bg-red-50 text-red-600 p-3 rounded text-sm text-center">
                            {error}
                        </div>
                    )}
                    <div className="rounded-md shadow-sm -space-y-px">
                        <div>
                            <label htmlFor="email-address" className="sr-only">
                                {t('email')}
                            </label>
                            <input
                                id="email-address"
                                name="email"
                                type="email"
                                autoComplete="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-primary focus:border-primary focus:z-10 sm:text-sm"
                                placeholder={t('email')}
                            />
                        </div>
                        <div>
                            <label htmlFor="password" className="sr-only">
                                {t('password')}
                            </label>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                autoComplete="current-password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-primary focus:border-primary focus:z-10 sm:text-sm"
                                placeholder={t('password')}
                            />
                        </div>
                    </div>

                    <div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50"
                        >
                            {loading ? "..." : t('submit_login')}
                        </button>
                    </div>

                    <div className="text-center text-sm">
                        <span className="text-gray-600">{t('no_account')} </span>
                        <Link href="/auth/register" className="font-medium text-primary hover:text-primary-dark">
                            {t('register_link')}
                        </Link>
                    </div>
                </form>
            </div>
        </div>
    );
}
