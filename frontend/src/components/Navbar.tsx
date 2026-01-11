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
        <nav className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50 shadow-sm">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    {/* Logo */}
                    <div className="flex items-center">
                        <Link href="/" className="flex-shrink-0 flex items-center gap-2">
                            <img
                                src="/Company360_logo_Color_PNG_bez_aizsarglaukumu-.png"
                                alt="Company 360"
                                className="h-14 w-auto"
                            />
                        </Link>
                    </div>

                    {/* Desktop Navigation */}
                    <div className="hidden lg:flex items-center gap-4">
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
                            {t('personas')}
                        </Link>
                        <Link
                            href="/mvk-declaration"
                            className="text-gray-600 hover:text-primary transition-colors text-sm font-medium whitespace-nowrap inline-flex items-center gap-1.5"
                        >
                            {t('mvk')}
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">
                                Beta
                            </span>
                        </Link>
                        <Link
                            href="/pricing"
                            className="text-gray-600 hover:text-primary transition-colors text-sm font-medium whitespace-nowrap inline-flex items-center gap-1.5"
                        >
                            {t('pricing')}
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">
                                Beta
                            </span>
                        </Link>

                        <div className="h-6 w-px bg-gray-200 mx-2" />

                        {isLoggedIn && (
                            <Link
                                href="/dashboard"
                                className="p-2 text-gray-600 hover:text-primary transition-colors rounded-full hover:bg-gray-100"
                                title={t('profile')}
                            >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                </svg>
                            </Link>
                        )}

                        <LanguageSwitcher />

                        {isLoggedIn ? (
                            <button
                                onClick={handleLogout}
                                className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors shadow-sm"
                            >
                                {t('logout')}
                            </button>
                        ) : (
                            <Link href="/auth/login" className="inline-flex items-center gap-2 px-4 py-2 border border-transparent rounded-lg text-sm font-medium text-white bg-slate-900 hover:bg-slate-800 transition-colors shadow-sm">
                                {t('login')}
                            </Link>
                        )}
                    </div>

                    {/* Mobile Menu Button - Visible ONLY on small screens */}
                    <div className="flex lg:hidden items-center gap-2">
                        <div className="block lg:hidden">
                            <LanguageSwitcher />
                        </div>
                        <button
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                            className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors lg:hidden"
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
                    <div className="lg:hidden bg-white border-t border-gray-100 shadow-lg">
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
                                href="/personas"
                                onClick={() => setIsMenuOpen(false)}
                                className="block px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors font-medium"
                            >
                                {t('personas')}
                            </Link>
                            <Link
                                href="/mvk-declaration"
                                onClick={() => setIsMenuOpen(false)}
                                className="flex items-center justify-between px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors font-medium"
                            >
                                {t('mvk')}
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-700 uppercase tracking-wider">Beta</span>
                            </Link>
                            <Link
                                href="/pricing"
                                onClick={() => setIsMenuOpen(false)}
                                className="flex items-center justify-between px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors font-medium"
                            >
                                {t('pricing')}
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-700 uppercase tracking-wider">Beta</span>
                            </Link>

                            {isLoggedIn ? (
                                <div className="pt-2 space-y-2">
                                    <Link
                                        href="/dashboard"
                                        onClick={() => setIsMenuOpen(false)}
                                        className="flex items-center gap-2 px-3 py-2 rounded-lg text-primary hover:bg-primary/5 transition-colors font-medium"
                                    >
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                        </svg>
                                        {t('profile')}
                                    </Link>
                                    <button
                                        onClick={handleLogout}
                                        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors shadow-sm"
                                    >
                                        {t('logout')}
                                    </button>
                                </div>
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
