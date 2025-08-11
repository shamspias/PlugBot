'use client';

import {useAuth} from '@/contexts/AuthContext';
import {useTranslations} from 'next-intl';
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {LogOut, User} from 'lucide-react';
import LanguageSwitcher from './LanguageSwitcher';

export default function Navigation() {
    const {user, logout} = useAuth();
    const pathname = usePathname();
    const t = useTranslations('nav');

    // Don't show navigation on auth pages
    if (pathname.includes('/auth')) {
        return null;
    }

    if (!user) {
        return null;
    }

    return (
        <nav className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex items-center">
                        <Link href="/dashboard" className="text-xl font-bold text-gray-900">
                            {t('title')}
                        </Link>
                    </div>

                    <div className="flex items-center space-x-4">
                        <LanguageSwitcher/>

                        <div className="flex items-center space-x-2 text-sm text-gray-700">
                            <User className="w-4 h-4"/>
                            <span>{user.email}</span>
                        </div>

                        <button
                            onClick={logout}
                            className="flex items-center space-x-2 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                        >
                            <LogOut className="w-4 h-4"/>
                            <span>{t('logout')}</span>
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
}