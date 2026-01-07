"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Link, useRouter } from "@/i18n/routing";
import Cookies from "js-cookie";

// Reusable promotional panel component
const PromotionalPanel = () => (
    <div className="hidden lg:flex w-1/2 bg-[#0f172a] relative overflow-hidden items-center justify-center">
        {/* Background effects */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 to-purple-900/20"></div>
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-full h-1/2 bg-gradient-to-t from-[#0f172a] to-transparent"></div>

        <div className="relative z-10 max-w-lg px-12 text-center text-white">
            {/* Chart Mockup Card */}
            <div className="mx-auto mb-10 w-80 bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/10 shadow-2xl transform rotate-3 hover:rotate-0 transition-transform duration-500">
                <div className="flex items-center gap-4 mb-5 border-b border-white/10 pb-4">
                    <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center text-green-400 font-bold text-sm">Top</div>
                    <div className="text-left">
                        <div className="text-sm font-bold text-white">Apgrozījuma dinamika</div>
                        <div className="text-xs text-gray-400">Pēdējie 5 gadi</div>
                    </div>
                </div>
                <div className="space-y-3">
                    <div className="flex items-end gap-2 h-24 pb-2 border-b border-white/5">
                        <div className="w-1/5 bg-white/20 rounded-t h-[40%]"></div>
                        <div className="w-1/5 bg-white/20 rounded-t h-[60%]"></div>
                        <div className="w-1/5 bg-white/30 rounded-t h-[50%]"></div>
                        <div className="w-1/5 bg-white/40 rounded-t h-[75%]"></div>
                        <div className="w-1/5 bg-green-500 rounded-t h-[90%]"></div>
                    </div>
                    <div className="flex justify-between text-[10px] text-gray-400">
                        <span>2020</span><span>2024</span>
                    </div>
                </div>
            </div>

            <h2 className="text-3xl font-bold mb-4 tracking-tight">Redzi to, ko citi palaiž garām</h2>
            <p className="text-gray-400 text-lg leading-relaxed mb-8">
                Pievienojies platformai, kas pārvērš publiskos datus reālā biznesa priekšrocībā. Atklāj slēptos riskus un iespējas.
            </p>

            {/* Trust signals */}
            <div className="pt-8 border-t border-white/10 flex justify-center gap-8 text-sm text-gray-400 font-medium">
                <span className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                    10,000+ lietotāji
                </span>
                <span className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                    Droši dati
                </span>
            </div>
        </div>
    </div>
);

// Google SVG Icon
const GoogleIcon = () => (
    <svg className="w-5 h-5" viewBox="0 0 24 24">
        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
);

// LinkedIn SVG Icon
const LinkedInIcon = () => (
    <svg className="w-5 h-5 text-[#0077b5] fill-current" viewBox="0 0 24 24">
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
);

export default function LoginPage() {
    const t = useTranslations('Auth');
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);

            const res = await fetch('/api/auth/login', {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || t('error_generic'));
            }

            const data = await res.json();
            Cookies.set('token', data.access_token, { expires: 30 });
            router.refresh();
            router.push('/');
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSocialLogin = (provider: string) => {
        // TODO: Implement OAuth flow
        alert(`${provider} login coming soon!`);
    };

    return (
        <div className="min-h-screen w-full flex">
            {/* Left Side - Form */}
            <div className="w-full lg:w-1/2 flex flex-col justify-center px-8 md:px-16 lg:px-24 bg-white relative">
                {/* Logo */}
                <div className="absolute top-8 left-8 lg:left-12 flex items-center gap-2">
                    <div className="w-8 h-8 bg-[#0f172a] rounded-lg flex items-center justify-center text-white font-bold text-sm">
                        360
                    </div>
                    <span className="text-xl font-bold text-gray-900 tracking-tight">Company 360</span>
                </div>

                <div className="max-w-md w-full mx-auto pt-24 lg:pt-8">
                    {/* Header */}
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Laipni lūgti atpakaļ</h1>
                        <p className="mt-2 text-sm text-gray-600">Ievadiet savus datus, lai piekļūtu analītikai.</p>
                    </div>

                    {/* Social Login Buttons */}
                    <div className="grid grid-cols-2 gap-3 mb-6">
                        <button
                            onClick={() => handleSocialLogin('Google')}
                            className="flex items-center justify-center gap-2 py-2.5 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700"
                        >
                            <GoogleIcon />
                            Google
                        </button>
                        <button
                            onClick={() => handleSocialLogin('LinkedIn')}
                            className="flex items-center justify-center gap-2 py-2.5 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700"
                        >
                            <LinkedInIcon />
                            LinkedIn
                        </button>
                    </div>

                    {/* Divider */}
                    <div className="relative mb-6">
                        <div className="absolute inset-0 flex items-center">
                            <span className="w-full border-t border-gray-200"></span>
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="bg-white px-2 text-gray-500">vai ar e-pastu</span>
                        </div>
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm text-center mb-4">
                            {error}
                        </div>
                    )}

                    {/* Login Form */}
                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">E-pasts</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:border-blue-600 outline-none transition-all"
                                placeholder="janis@uznemums.lv"
                            />
                        </div>
                        <div>
                            <div className="flex items-center justify-between mb-1">
                                <label className="block text-sm font-medium text-gray-700">Parole</label>
                                <Link href="/auth/forgot-password" className="text-sm font-medium text-blue-600 hover:text-blue-500">
                                    Aizmirsi?
                                </Link>
                            </div>
                            <div className="relative">
                                <input
                                    type={showPassword ? "text" : "password"}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 focus:border-blue-600 outline-none transition-all pr-12"
                                    placeholder="••••••••"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                >
                                    {showPassword ? (
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                                        </svg>
                                    ) : (
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                        </svg>
                                    )}
                                </button>
                            </div>
                        </div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 px-4 bg-[#0f172a] hover:bg-[#1e293b] text-white rounded-lg font-semibold shadow-lg shadow-gray-900/10 transition-all transform hover:-translate-y-0.5 disabled:opacity-50"
                        >
                            {loading ? "Lūdzu uzgaidiet..." : "Pieslēgties"}
                        </button>
                    </form>

                    {/* Register Link */}
                    <p className="mt-8 text-center text-sm text-gray-600">
                        Nav konta?{' '}
                        <Link href="/auth/register" className="font-semibold text-blue-600 hover:underline">
                            Reģistrējies bez maksas
                        </Link>
                    </p>
                </div>
            </div>

            {/* Right Side - Promotional */}
            <PromotionalPanel />
        </div>
    );
}
