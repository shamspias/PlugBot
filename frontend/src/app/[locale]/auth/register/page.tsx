'use client';

import React, {useState} from 'react';
import {useAuth} from '@/contexts/AuthContext';
import Link from 'next/link';
import {Mail, Lock, User, Eye, EyeOff, UserPlus, AlertCircle, CheckCircle} from 'lucide-react';
import {useTranslations} from 'next-intl';

export default function RegisterPage() {
    const t = useTranslations('auth.register');
    const {register} = useAuth();

    const [formData, setFormData] = useState({
        email: '',
        username: '',
        password: '',
        confirmPassword: '',
        full_name: ''
    });
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string>('');
    const [passwordStrength, setPasswordStrength] = useState(0);

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

        if (name === 'password') checkPasswordStrength(value);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (formData.password !== formData.confirmPassword) {
            setError(t('errors.passwordMismatch'));
            return;
        }

        if (passwordStrength < 5) {
            setError(t('errors.weakPassword'));
            return;
        }

        setLoading(true);

        try {
            await register({
                email: formData.email,
                username: formData.username,
                password: formData.password,
                full_name: formData.full_name || undefined
            });
        } catch (err: any) {
            setError(err?.message || t('errors.registrationFailed'));
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

    const strengthLabel =
        passwordStrength <= 2
            ? t('passwordStrength.weak')
            : passwordStrength <= 3
                ? t('passwordStrength.fair')
                : passwordStrength <= 4
                    ? t('passwordStrength.good')
                    : t('passwordStrength.strong');

    return (
        <div
            className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-white to-blue-50 py-12">
            <div
                className="absolute inset-0 bg-grid-slate-100 [mask-image:radial-gradient(ellipse_at_center,white,transparent)] -z-10"/>

            <div className="w-full max-w-md">
                <div className="bg-white rounded-2xl shadow-xl p-8 backdrop-blur-lg bg-white/95">
                    {/* Logo & Title */}
                    <div className="text-center mb-8">
                        <div
                            className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-600 rounded-2xl mb-4">
                            <UserPlus className="w-8 h-8 text-white"/>
                        </div>
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                            {t('title')}
                        </h1>
                        <p className="text-gray-600 mt-2">{t('subtitle')}</p>
                    </div>

                    {/* Error Alert */}
                    {error && (
                        <div
                            role="alert"
                            className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3"
                        >
                            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"/>
                            <p className="text-sm text-red-700">{error}</p>
                        </div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-5" noValidate>
                        <div>
                            <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 mb-2">
                                {t('fullNameOptional')}
                            </label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"/>
                                <input
                                    id="full_name"
                                    type="text"
                                    name="full_name"
                                    value={formData.full_name}
                                    onChange={handleChange}
                                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                                    placeholder={t('placeholders.fullName')}
                                    autoComplete="name"
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                                {t('username')}
                            </label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"/>
                                <input
                                    id="username"
                                    type="text"
                                    name="username"
                                    value={formData.username}
                                    onChange={handleChange}
                                    required
                                    pattern="^[a-zA-Z0-9_-]+$"
                                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                                    placeholder={t('placeholders.username')}
                                    autoComplete="username"
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                                {t('email')}
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"/>
                                <input
                                    id="email"
                                    type="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    required
                                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                                    placeholder={t('placeholders.email')}
                                    autoComplete="email"
                                    inputMode="email"
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                                {t('password')}
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"/>
                                <input
                                    id="password"
                                    type={showPassword ? 'text' : 'password'}
                                    name="password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    required
                                    className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                                    placeholder={t('placeholders.password')}
                                    autoComplete="new-password"
                                    aria-describedby="password-strength password-requirements"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                    aria-label={showPassword ? t('hidePassword') : t('showPassword')}
                                >
                                    {showPassword ? <EyeOff className="w-5 h-5"/> : <Eye className="w-5 h-5"/>}
                                </button>
                            </div>

                            {/* Password Strength Indicator */}
                            {formData.password && (
                                <div className="mt-2">
                                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden" aria-hidden="true">
                                        <div
                                            className={`h-full transition-all ${getPasswordStrengthColor()}`}
                                            style={{width: `${(passwordStrength / 5) * 100}%`}}
                                        />
                                    </div>
                                    <span id="password-strength" className="mt-1 block text-xs text-gray-600">
                    {strengthLabel}
                  </span>
                                    <div id="password-requirements" className="mt-2 space-y-1">
                                        {[
                                            {check: formData.password.length >= 8, text: t('requirements.minChars')},
                                            {check: /[A-Z]/.test(formData.password), text: t('requirements.uppercase')},
                                            {check: /[a-z]/.test(formData.password), text: t('requirements.lowercase')},
                                            {check: /\d/.test(formData.password), text: t('requirements.number')},
                                            {
                                                check: /[!@#$%^&*(),.?":{}|<>]/.test(formData.password),
                                                text: t('requirements.special')
                                            }
                                        ].map((req, idx) => (
                                            <div key={idx} className="flex items-center gap-2 text-xs">
                                                <CheckCircle
                                                    className={`w-3 h-3 ${req.check ? 'text-green-500' : 'text-gray-300'}`}/>
                                                <span
                                                    className={req.check ? 'text-green-700' : 'text-gray-500'}>{req.text}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        <div>
                            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                                {t('confirmPassword')}
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"/>
                                <input
                                    id="confirmPassword"
                                    type={showPassword ? 'text' : 'password'}
                                    name="confirmPassword"
                                    value={formData.confirmPassword}
                                    onChange={handleChange}
                                    required
                                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                                    placeholder={t('placeholders.confirmPassword')}
                                    autoComplete="new-password"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading || passwordStrength < 5}
                            className="w-full py-3 px-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium rounded-lg hover:from-purple-700 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? (
                                <span className="flex items-center justify-center">
                  <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                  >
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                            strokeWidth="4"></circle>
                    <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                                    {t('creatingAccount')}
                </span>
                            ) : (
                                t('createAccount')
                            )}
                        </button>
                    </form>

                    {/* Login Link */}
                    <p className="mt-6 text-center text-gray-600">
                        {t('alreadyHaveAccount')}{' '}
                        <Link href="/auth/login" className="text-purple-600 hover:text-purple-700 font-medium">
                            {t('signIn')}
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
