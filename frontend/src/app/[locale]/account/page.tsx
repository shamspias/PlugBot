'use client';

import React, {useEffect, useState} from 'react';
import {useLocale} from 'next-intl';
import ProtectedRoute from '@/components/ProtectedRoute';
import {useAuth} from '@/contexts/AuthContext';
import {apiClient} from '@/lib/api/client';
import {Lock, Save, User as UserIcon, ShieldCheck} from 'lucide-react';

export default function AccountPage() {
    const {user} = useAuth();
    const locale = useLocale();

    // Profile form state
    const [username, setUsername] = useState('');
    const [fullName, setFullName] = useState('');
    const [savingProfile, setSavingProfile] = useState(false);
    const [profileMsg, setProfileMsg] = useState<string | null>(null);

    // Password form state
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmNewPassword, setConfirmNewPassword] = useState('');
    const [changingPw, setChangingPw] = useState(false);
    const [pwMsg, setPwMsg] = useState<string | null>(null);

    useEffect(() => {
        if (user) {
            setUsername(user.username || '');
            setFullName(user.full_name || '');
        }
    }, [user]);

    const handleSaveProfile = async (e: React.FormEvent) => {
        e.preventDefault();
        setProfileMsg(null);
        setSavingProfile(true);
        try {
            await apiClient.updateProfile({username, full_name: fullName || undefined});
            setProfileMsg('Profile updated');
        } catch (err: any) {
            setProfileMsg(err?.message || 'Failed to update profile');
        } finally {
            setSavingProfile(false);
        }
    };

    const handleChangePassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setPwMsg(null);

        if (newPassword !== confirmNewPassword) {
            setPwMsg('New passwords do not match');
            return;
        }

        setChangingPw(true);
        try {
            await apiClient.changePassword({current_password: currentPassword, new_password: newPassword});
            setPwMsg('Password changed');
            setCurrentPassword('');
            setNewPassword('');
            setConfirmNewPassword('');
        } catch (err: any) {
            setPwMsg(err?.message || 'Failed to change password');
        } finally {
            setChangingPw(false);
        }
    };

    return (
        <ProtectedRoute>
            <div className="max-w-3xl mx-auto px-4 py-10">
                <div className="mb-8">
                    <h1 className="text-2xl font-bold">Account</h1>
                    <p className="text-gray-600">Manage your profile and password.</p>
                </div>

                <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
                    {/* Profile */}
                    <div className="bg-white rounded-2xl shadow-sm border p-6">
                        <div className="flex items-center gap-2 mb-4">
                            <UserIcon className="w-5 h-5"/>
                            <h2 className="font-semibold">Profile</h2>
                        </div>
                        {profileMsg && (
                            <div
                                className="mb-4 text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
                                {profileMsg}
                            </div>
                        )}
                        <form onSubmit={handleSaveProfile} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                                <input
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    required
                                    pattern="^[a-zA-Z0-9_-]+$"
                                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="your_username"
                                    autoComplete="username"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Full name</label>
                                <input
                                    value={fullName}
                                    onChange={(e) => setFullName(e.target.value)}
                                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Your name (optional)"
                                    autoComplete="name"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={savingProfile}
                                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                            >
                                <Save className="w-4 h-4"/> Save
                            </button>
                        </form>
                    </div>

                    {/* Change Password */}
                    <div className="bg-white rounded-2xl shadow-sm border p-6">
                        <div className="flex items-center gap-2 mb-4">
                            <Lock className="w-5 h-5"/>
                            <h2 className="font-semibold">Change password</h2>
                        </div>
                        {pwMsg && (
                            <div
                                className={`mb-4 text-sm rounded-lg px-3 py-2 ${pwMsg.includes('changed') ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                                {pwMsg}
                            </div>
                        )}
                        <form onSubmit={handleChangePassword} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Current password</label>
                                <input
                                    type="password"
                                    value={currentPassword}
                                    onChange={(e) => setCurrentPassword(e.target.value)}
                                    required
                                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    autoComplete="current-password"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">New password</label>
                                <input
                                    type="password"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    required
                                    minLength={8}
                                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    autoComplete="new-password"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Confirm new
                                    password</label>
                                <input
                                    type="password"
                                    value={confirmNewPassword}
                                    onChange={(e) => setConfirmNewPassword(e.target.value)}
                                    required
                                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    autoComplete="new-password"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={changingPw}
                                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                            >
                                <ShieldCheck className="w-4 h-4"/> Update password
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </ProtectedRoute>
    );
}
