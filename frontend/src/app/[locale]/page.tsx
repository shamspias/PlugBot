'use client';

import {useEffect} from 'react';
import {useRouter} from 'next/navigation';
import {useLocale} from 'next-intl';
import {useAuth} from '@/contexts/AuthContext';

export default function Home() {
    const {user, loading} = useAuth();
    const router = useRouter();
    const locale = useLocale();

    useEffect(() => {
        if (loading) return;

        const targetPath = user
            ? `/${locale}/dashboard`
            : `/${locale}/auth/login`;

        // Avoid redundant navigation if we're already there
        if (typeof window !== 'undefined' && window.location.pathname !== targetPath) {
            router.replace(targetPath);
        }
    }, [user, loading, router, locale]);

    // Simple spinner shown while we resolve auth + navigate
    return (
        <div className="min-h-screen flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
    );
}
