'use client';

import {useEffect} from 'react';
import {useRouter, usePathname, useSearchParams} from 'next/navigation';
import {useLocale} from 'next-intl';
import type {ReactNode} from 'react';
import {useAuth} from '@/contexts/AuthContext';

export default function ProtectedRoute({children}: { children: ReactNode }) {
    const {user, loading} = useAuth();
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const locale = useLocale();

    const loginPath = `/${locale}/auth/login`;
    const dashboardPath = `/${locale}/dashboard`;

    const isOnLogin = pathname?.startsWith(loginPath) ?? false;
    const isOnAnyAuthRoute = pathname?.startsWith(`/${locale}/auth`) ?? false;

    useEffect(() => {
        if (loading) return;

        // If not authenticated, send to locale-aware login (avoid loop if already there)
        if (!user) {
            if (!isOnLogin) {
                const current = pathname + (searchParams?.toString() ? `?${searchParams.toString()}` : '');
                const url = `${loginPath}?returnTo=${encodeURIComponent(current || `/${locale}`)}`;
                router.replace(url);
            }
            return;
        }

        // If authenticated but on an auth screen, send to locale-aware dashboard
        if (isOnAnyAuthRoute) {
            router.replace(dashboardPath);
        }
    }, [
        user,
        loading,
        router,
        locale,
        pathname,
        searchParams,
        isOnLogin,
        isOnAnyAuthRoute,
        loginPath,
        dashboardPath,
    ]);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"/>
            </div>
        );
    }

    // While redirecting unauthenticated users away from protected routes, render nothing
    if (!user) return null;

    return <>{children}</>;
}
