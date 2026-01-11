"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { Link, useRouter } from "@/i18n/routing";
import { useTranslations } from "next-intl";

export default function ResetPasswordPage() {
    const t = useTranslations('Auth');
    const router = useRouter();
    const searchParams = useSearchParams();
    const token = searchParams.get("token");

    const [loading, setLoading] = useState(false);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    // If no token, we show "Request Reset" form
    const isRequestMode = !token;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            if (isRequestMode) {
                // Request Password Reset
                const res = await fetch('/api/auth/forgot-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email }),
                });

                if (!res.ok) throw new Error("Kļūda nosūtot pieprasījumu");
                setSuccess(true);
            } else {
                // Reset Password with Token
                if (password !== confirmPassword) {
                    throw new Error("Paroles nesakrīt");
                }

                const res = await fetch('/api/auth/reset-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token, new_password: password }),
                });

                if (!res.ok) throw new Error("Neizdevās atjaunot paroli");
                setSuccess(true);
            }
        } catch (err: any) {
            setError(err.message || "Notika kļūda");
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
                <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-lg text-center">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">
                        {isRequestMode ? "Pārbaudiet e-pastu" : "Parole atjaunota!"}
                    </h2>
                    <p className="text-gray-600 mb-6">
                        {isRequestMode
                            ? "Nosūtījām instrukcijas paroles atjaunošanai uz norādīto e-pastu."
                            : "Jūsu parole ir veiksmīgi nomainīta. Varat pieslēgties ar jauno paroli."}
                    </p>
                    <Link
                        href="/auth/login"
                        className="inline-block w-full py-3 px-4 bg-[#0f172a] hover:bg-[#1e293b] text-white rounded-lg font-semibold transition-colors"
                    >
                        Atgriezties pie pieslēgšanās
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
            <div className="w-full max-w-md bg-white rounded-xl shadow-lg p-8">
                {/* Logo */}
                <div className="flex justify-center mb-8">
                    <Link href="/" className="block w-40 hover:opacity-90 transition-opacity">
                        <img
                            src="/Company360_logo_Color_PNG_bez_aizsarglaukumu-.png"
                            alt="Company 360"
                            className="w-full h-auto"
                        />
                    </Link>
                </div>

                <h1 className="text-2xl font-bold text-gray-900 text-center mb-2">
                    {isRequestMode ? "Atjaunot paroli" : "Izveidot jaunu paroli"}
                </h1>
                <p className="text-sm text-gray-600 text-center mb-8">
                    {isRequestMode
                        ? "Ievadiet e-pastu, lai saņemtu instrukcijas."
                        : "Lūdzu, ievadiet jauno paroli zemāk."}
                </p>

                {error && (
                    <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm text-center mb-6">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    {isRequestMode ? (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">E-pasts</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 outline-none"
                                placeholder="janis@uznemums.lv"
                            />
                        </div>
                    ) : (
                        <>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Jaunā parole</label>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    minLength={8}
                                    className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 outline-none"
                                    placeholder="••••••••"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Atkārtojiet paroli</label>
                                <input
                                    type="password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    required
                                    className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-600 outline-none"
                                    placeholder="••••••••"
                                />
                            </div>
                        </>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-3 px-4 bg-[#0f172a] hover:bg-[#1e293b] text-white rounded-lg font-semibold shadow-lg transition-all disabled:opacity-50"
                    >
                        {loading ? "Apstrādā..." : (isRequestMode ? "Nosūtīt saiti" : "Mainīt paroli")}
                    </button>

                    <div className="text-center mt-6">
                        <Link href="/auth/login" className="text-sm font-medium text-gray-600 hover:text-gray-900">
                            ← Atgriezties
                        </Link>
                    </div>
                </form>
            </div>
        </div>
    );
}
