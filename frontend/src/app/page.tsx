'use client';

import {useAuth} from '@/contexts/AuthContext';
import {useRouter} from 'next/navigation';
import {useEffect} from 'react';

export default function Home() {
    const {user, loading} = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!loading) {
            if (user) {
                router.push('/dashboard');
            } else {
                router.push('/auth/login');
            }
        }
    }, [user, loading, router]);

    return (
        <div className="min-h-screen flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
    );
}