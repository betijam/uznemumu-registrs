"use client";

import { useState, useEffect } from "react";
import { Link, useRouter } from "@/i18n/routing";
import { useTranslations } from "next-intl";
import Cookies from "js-cookie";

import LanguageSwitcher from "@/components/LanguageSwitcher";

export default function Navbar() {
    const t = useTranslations('Navigation');
    const tAuth = useTranslations('Auth');
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const router = useRouter();

    useEffect(() => {
        const token = Cookies.get('token');
        setIsLoggedIn(!!token);
    }, []);

    const handleLogout = () => {
        Cookies.remove('token');
        setIsLoggedIn(false);
        router.refresh();
        router.push('/');
    };

    return (
        <nav className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    {/* Logo */}
                    <div className="flex items-center">
                        <Link href="/" className="flex-shrink-0 flex items-center gap-2">
                            <div className="w-8 h-8 bg-gradient-to-br from-accent to-primary rounded-lg flex items-center justify-center">
                                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                                </svg>
                            </div>
                            <span className="text-lg sm:text-xl font-bold text-primary whitespace-nowrap">Company 360</span>
                        </Link>
                    </div>

                    {/* Desktop Navigation */}
                    <div className="hidden sm:flex items-center gap-4">
                        <Link
                            href="/"
                            className="text-gray-600 hover:text-primary transition-colors text-sm font-medium"
                        >
                            {t('home')}
                        </Link>
                        <Link
                            href="/industries"
                            className="text-gray-600 hover:text-primary transition-colors text-sm font-medium whitespace-nowrap"
                        >
                            {t('industries')}
                        </Link>
                        <Link
                            href="/regions"
                            className="text-gray-600 hover:text-primary transition-colors text-sm font-medium whitespace-nowrap"
                        >
                            {t('regions')}
                        </Link>
                        <Link
                            href="/explore"
                            className="text-gray-600 hover:text-primary transition-colors text-sm font-medium whitespace-nowrap"
                        >
                            {t('analytics')}
                        </Link>
                        <Link
                            href="/personas"
                            className="text-gray-600 hover:text-primary transition-colors text-sm font-medium whitespace-nowrap"
                        >
                            Personas
                        </Link>
                        <Link
                            href="/mvk-declaration"
                            className="text-gray-600 hover:text-primary transition-colors text-sm font-medium whitespace-nowrap"
                        >
                            {t('mvk')}
                        </Link>
                        <LanguageSwitcher />

                        {isLoggedIn ? (
                            <button
                                onClick={handleLogout}
                                className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors shadow-sm"
                            >
                                Logout
                            </button>
                        ) : (
                            <Link href="/auth/login" className="inline-flex items-center gap-2 px-4 py-2 border border-transparent rounded-lg text-sm font-medium text-white bg-primary hover:bg-secondary transition-colors shadow-sm">
                                {t('login')}
                            </Link>
                        )}
                    </div>

                    {/* Mobile Menu Button - Visible ONLY on small screens */}
                    <div className="flex sm:hidden items-center gap-4">
                        <div className="block sm:hidden">
                            <LanguageSwitcher />
                        </div>
                        <button
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                            className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors sm:hidden"
                            aria-label="Toggle menu"
                        >
                            {isMenuOpen ? (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            ) : (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                </svg>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile Menu Dropdown */}
            {
                isMenuOpen && (
                    <div className="sm:hidden bg-white border-t border-gray-100 shadow-lg">
                        <div className="px-4 py-3 space-y-2">
                            <Link
                                href="/"
                                onClick={() => setIsMenuOpen(false)}
                                className="block px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors font-medium"
                            >
                                {t('home')}
                            </Link>
                            <Link
                                href="/industries"
                                onClick={() => setIsMenuOpen(false)}
                                className="block px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors font-medium"
                            >
                                {t('industries')}
                            </Link>
                            <Link
                                href="/explore"
                                onClick={() => setIsMenuOpen(false)}
                                className="block px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors font-medium"
                            >
                                {t('analytics')}
                            </Link>
                            <Link
                                href="/regions"
                                onClick={() => setIsMenuOpen(false)}
                                className="block px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors font-medium"
                            >
                                {t('regions')}
                            </Link>
                            <Link
                                href="/mvk-declaration"
                                onClick={() => setIsMenuOpen(false)}
                                className="block px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors font-medium"
                            >
                                {t('mvk')}
                            </Link>

                            {isLoggedIn ? (
                                <button
                                    onClick={handleLogout}
                                    className="w-full mt-2 px-4 py-2.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors shadow-sm"
                                >
                                    Logout
                                </button>
                            ) : (
                                <Link href="/auth/login" className="block w-full mt-2 px-4 py-2.5 border border-transparent rounded-lg text-sm font-medium text-white bg-primary hover:bg-secondary transition-colors shadow-sm text-center">
                                    {t('login')}
                                </Link>
                            )}
                        </div>
                    </div>
                )
            }
        </nav >
    );
}
