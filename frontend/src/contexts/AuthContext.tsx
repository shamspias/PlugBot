'use client';

import React, {createContext, useContext, useState, useEffect, ReactNode} from 'react';
import {apiClient} from '@/lib/api/client';
import {useRouter} from 'next/navigation';

interface User {
    id: string;
    email: string;
    username: string;
    full_name?: string;
    is_superuser: boolean;
    email_verified: boolean;
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    register: (data: RegisterData) => Promise<void>;
    refreshToken: () => Promise<void>;
}

interface RegisterData {
    email: string;
    username: string;
    password: string;
    full_name?: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({children}: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                setLoading(false);
                return;
            }

            const userData = await apiClient.getCurrentUser();
            setUser(userData);
        } catch (error) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
        } finally {
            setLoading(false);
        }
    };

    const login = async (email: string, password: string) => {
        const response = await apiClient.login(email, password);
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('refresh_token', response.refresh_token);

        const userData = await apiClient.getCurrentUser();
        setUser(userData);
        router.push('/dashboard');
    };

    const logout = async () => {
        try {
            await apiClient.logout();
        } finally {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            setUser(null);
            router.push('/auth/login');
        }
    };

    const register = async (data: RegisterData) => {
        await apiClient.register(data);
        // Auto login after registration
        await login(data.email, data.password);
    };

    const refreshToken = async () => {
        try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (!refreshToken) throw new Error('No refresh token');

            const response = await apiClient.refreshAccessToken(refreshToken);
            localStorage.setItem('access_token', response.access_token);
            localStorage.setItem('refresh_token', response.refresh_token);
        } catch (error) {
            await logout();
        }
    };

    return (
        <AuthContext.Provider value={{user, loading, login, logout, register, refreshToken}}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};