'use client';

import React, {useState} from 'react';
import Link from 'next/link';
import {Mail, ArrowLeft, CheckCircle} from 'lucide-react';
import {useTranslations} from 'next-intl';
import {apiClient} from '@/lib/api/client';

export default function ForgotPasswordPage() {
    const t = useTranslations('auth.forgotPassword');

    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [submitted, setSubmitted] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await apiClient.requestPasswordReset(email);
            setSubmitted(true);
        } catch (err: any) {
            // Show server message if present, otherwise a generic one (translated if you add the key)
            setError(
                err?.message ||
                (t.has('errors.generic') ? t('errors.generic') : 'Failed to send reset email')
            );

        } finally {
            setLoading(false);
        }
    };

    if (submitted) {
        return (
            <div
                className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 via-white to-blue-50">
                <div className="w-full max-w-md">
                    <div className="bg-white rounded-2xl shadow-xl p-8">
                        <div className="text-center">
                            <div
                                className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                                <CheckCircle className="w-8 h-8 text-green-600"/>
                            </div>
                            <h2 className="text-2xl font-bold text-gray-900 mb-2">
                                {t('checkEmail.title')}
                            </h2>
                            <p className="text-gray-600 mb-6">
                                {t('checkEmail.message')}{' '}
                                <strong>{email}</strong>
                            </p>
                            <Link
                                href="/auth/login"
                                className="inline-flex items-center text-blue-600 hover:text-blue-700 font-medium"
                            >
                                <ArrowLeft className="w-4 h-4 mr-2"/>
                                {t('checkEmail.backToLogin')}
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div
            className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50">
            <div className="w-full max-w-md">
                <div className="bg-white rounded-2xl shadow-xl p-8">
                    <div className="text-center mb-8">
                        <h1 className="text-3xl font-bold text-gray-900">
                            {t('title')}
                        </h1>
                        <p className="text-gray-600 mt-2">
                            {t('subtitle')}
                        </p>
                    </div>

                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                            <p className="text-sm text-red-700">{error}</p>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label
                                htmlFor="email"
                                className="block text-sm font-medium text-gray-700 mb-2"
                            >
                                {t('email')}
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"/>
                                <input
                                    id="email"
                                    type="email"
                                    autoComplete="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="you@example.com"
                                    aria-label={t('email')}
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-all disabled:opacity-50"
                        >
                            {loading ? t('sending') : t('sendResetLink')}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <Link
                            href="/auth/login"
                            className="text-blue-600 hover:text-blue-700 font-medium"
                        >
                            {t('backToLogin')}
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
