'use client';

import React, {useState, useEffect, Suspense} from 'react';
import {useRouter, useSearchParams} from 'next/navigation';
import Link from 'next/link';
import {Lock, Eye, EyeOff, CheckCircle, AlertCircle, Shield, KeyRound} from 'lucide-react';
import {apiClient} from '@/lib/api/client';
import {useTranslations} from 'next-intl';

function ResetPasswordForm() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const token = searchParams.get('token');
    const t = useTranslations('auth.resetPassword');

    const [formData, setFormData] = useState({
        password: '',
        confirmPassword: ''
    });
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [passwordStrength, setPasswordStrength] = useState(0);
    const [tokenValid, setTokenValid] = useState<boolean | null>(null);

    useEffect(() => {
        if (!token) {
            setError(t('errors.invalidToken'));
            setTokenValid(false);
        } else {
            setTokenValid(true);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token]);

    const checkPasswordStrength = (password: string) => {
        let strength = 0;
        if (password.length >= 8) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/[a-z]/.test(password)) strength++;
        if (/\d/.test(password)) strength++;
        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++;
        setPasswordStrength(strength);
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const {name, value} = e.target;
        setFormData(prev => ({...prev, [name]: value}));

        if (name === 'password') {
            checkPasswordStrength(value);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (!token) {
            setError(t('errors.invalidToken'));
            return;
        }

        if (formData.password !== formData.confirmPassword) {
            setError(t('errors.passwordMismatch'));
            return;
        }

        if (passwordStrength < 5) {
            setError('Password does not meet all security requirements');
            return;
        }

        setLoading(true);

        try {
            await apiClient.resetPassword(token, formData.password);
            setSuccess(true);

            // Redirect to login after 3 seconds
            setTimeout(() => {
                router.push('/auth/login');
            }, 3000);
        } catch (err: any) {
            if (err.message?.includes('expired') || err.message?.includes('invalid')) {
                setError(t('errors.invalidToken'));
            } else {
                setError(err.message || 'Failed to reset password');
            }
        } finally {
            setLoading(false);
        }
    };

    const getPasswordStrengthColor = () => {
        if (passwordStrength <= 2) return 'bg-red-500';
        if (passwordStrength <= 3) return 'bg-yellow-500';
        if (passwordStrength <= 4) return 'bg-blue-500';
        return 'bg-green-500';
    };

    const getPasswordStrengthText = () => {
        if (passwordStrength <= 2) return 'Weak';
        if (passwordStrength <= 3) return 'Fair';
        if (passwordStrength <= 4) return 'Good';
        return 'Strong';
    };

    // Success state
    if (success) {
        return (
            <div
                className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 via-white to-blue-50">
                <div
                    className="absolute inset-0 bg-grid-slate-100 [mask-image:radial-gradient(ellipse_at_center,white,transparent)] -z-10"/>

                <div className="w-full max-w-md">
                    <div className="bg-white rounded-2xl shadow-xl p-8 backdrop-blur-lg bg-white/95">
                        <div className="text-center">
                            <div
                                className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-6 animate-bounce">
                                <CheckCircle className="w-10 h-10 text-green-600"/>
                            </div>
                            <h2 className="text-3xl font-bold text-gray-900 mb-4">
                                {t('success.title')}
                            </h2>
                            <p className="text-gray-600 mb-6">
                                {t('success.message')}
                            </p>
                            <div className="flex justify-center">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
                            </div>
                            <p className="mt-6 text-sm text-gray-500">
                                {t('success.redirecting')}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Invalid token state
    if (tokenValid === false) {
        return (
            <div
                className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 via-white to-gray-50">
                <div
                    className="absolute inset-0 bg-grid-slate-100 [mask-image:radial-gradient(ellipse_at_center,white,transparent)] -z-10"/>

                <div className="w-full max-w-md">
                    <div className="bg-white rounded-2xl shadow-xl p-8 backdrop-blur-lg bg-white/95">
                        <div className="text-center">
                            <div
                                className="inline-flex items-center justify-center w-20 h-20 bg-red-100 rounded-full mb-6">
                                <AlertCircle className="w-10 h-10 text-red-600"/>
                            </div>
                            <h2 className="text-2xl font-bold text-gray-900 mb-4">
                                {t('errors.invalidToken')}
                            </h2>
                            <p className="text-gray-600 mb-6">
                                {t('errors.invalidToken')}
                            </p>
                            <div className="space-y-3">
                                <Link
                                    href="/auth/forgot-password"
                                    className="block w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-all text-center"
                                >
                                    {t('errors.requestNew')}
                                </Link>
                                <Link
                                    href="/auth/login"
                                    className="block w-full py-3 px-4 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-all text-center"
                                >
                                    Back to Login
                                </Link>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Main reset form
    return (
        <div
            className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-white to-blue-50">
            <div
                className="absolute inset-0 bg-grid-slate-100 [mask-image:radial-gradient(ellipse_at_center,white,transparent)] -z-10"/>

            <div className="w-full max-w-md">
                <div className="bg-white rounded-2xl shadow-xl p-8 backdrop-blur-lg bg-white/95">
                    {/* Header */}
                    <div className="text-center mb-8">
                        <div
                            className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-600 rounded-2xl mb-4">
                            <KeyRound className="w-8 h-8 text-white"/>
                        </div>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                            Reset Your Password
                        </h1>
                        <p className="text-gray-600 mt-2">Enter your new password below</p>
                    </div>

                    {/* Error Alert */}
                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"/>
                            <div>
                                <p className="text-sm text-red-700">{error}</p>
                                {error.includes(t('errors.invalidToken')) && (
                                    <Link
                                        href="/auth/forgot-password"
                                        className="text-sm text-red-800 underline mt-1 inline-block hover:text-red-900"
                                    >
                                        {t('errors.requestNew')} →
                                    </Link>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Security Notice */}
                    <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-3">
                        <Shield className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5"/>
                        <div className="text-sm text-blue-700">
                            <p className="font-medium mb-1">Security Requirements:</p>
                            <p>
                                Your new password must be different from your previous password and meet all security
                                criteria below.
                            </p>
                        </div>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                New Password
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"/>
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    name="password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    required
                                    className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                                    placeholder="••••••••"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                                >
                                    {showPassword ? <EyeOff className="w-5 h-5"/> : <Eye className="w-5 h-5"/>}
                                </button>
                            </div>

                            {/* Password Strength Indicator */}
                            {formData.password && (
                                <div className="mt-3">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-xs text-gray-500">Password Strength</span>
                                        <span
                                            className={`text-xs font-medium ${
                                                passwordStrength <= 2
                                                    ? 'text-red-600'
                                                    : passwordStrength <= 3
                                                        ? 'text-yellow-600'
                                                        : passwordStrength <= 4
                                                            ? 'text-blue-600'
                                                            : 'text-green-600'
                                            }`}
                                        >
                      {getPasswordStrengthText()}
                    </span>
                                    </div>
                                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full transition-all duration-300 ${getPasswordStrengthColor()}`}
                                            style={{width: `${(passwordStrength / 5) * 100}%`}}
                                        />
                                    </div>
                                    <div className="mt-3 space-y-1.5">
                                        {[
                                            {check: formData.password.length >= 8, text: 'At least 8 characters'},
                                            {check: /[A-Z]/.test(formData.password), text: 'One uppercase letter'},
                                            {check: /[a-z]/.test(formData.password), text: 'One lowercase letter'},
                                            {check: /\d/.test(formData.password), text: 'One number'},
                                            {
                                                check: /[!@#$%^&*(),.?":{}|<>]/.test(formData.password),
                                                text: 'One special character'
                                            }
                                        ].map((req, idx) => (
                                            <div key={idx} className="flex items-center gap-2 text-xs">
                                                <div
                                                    className={`w-4 h-4 rounded-full flex items-center justify-center ${
                                                        req.check ? 'bg-green-100' : 'bg-gray-100'
                                                    }`}
                                                >
                                                    <CheckCircle
                                                        className={`w-3 h-3 ${req.check ? 'text-green-600' : 'text-gray-400'}`}
                                                    />
                                                </div>
                                                <span
                                                    className={req.check ? 'text-green-700' : 'text-gray-500'}>{req.text}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Confirm New Password
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"/>
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    name="confirmPassword"
                                    value={formData.confirmPassword}
                                    onChange={handleChange}
                                    required
                                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                                    placeholder="••••••••"
                                />
                                {formData.password && formData.confirmPassword && (
                                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                                        {formData.password === formData.confirmPassword ? (
                                            <CheckCircle className="w-5 h-5 text-green-500"/>
                                        ) : (
                                            <AlertCircle className="w-5 h-5 text-red-500"/>
                                        )}
                                    </div>
                                )}
                            </div>
                            {formData.password &&
                                formData.confirmPassword &&
                                formData.password !== formData.confirmPassword && (
                                    <p className="mt-2 text-sm text-red-600">{t('errors.passwordMismatch')}</p>
                                )}
                        </div>

                        <button
                            type="submit"
                            disabled={loading || passwordStrength < 5 || formData.password !== formData.confirmPassword}
                            className="w-full py-3 px-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium rounded-lg hover:from-purple-700 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] active:scale-[0.98]"
                        >
                            {loading ? (
                                <span className="flex items-center justify-center">
                  <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                  >
                    <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                    ></circle>
                    <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                                    {t('resetting')}
                </span>
                            ) : (
                                t('resetPassword')
                            )}
                        </button>
                    </form>

                    {/* Back to Login Link */}
                    <div className="mt-6 text-center">
                        <Link href="/auth/login"
                              className="text-sm text-gray-600 hover:text-gray-800 transition-colors">
                            Remember your password?
                            <span
                                className="ml-1 text-purple-600 hover:text-purple-700 font-medium">Back to Login</span>
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function ResetPasswordPage() {
    return (
        <Suspense
            fallback={
                <div className="min-h-screen flex items-center justify-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                </div>
            }
        >
            <ResetPasswordForm/>
        </Suspense>
    );
}
