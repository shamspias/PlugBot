'use client';

import React, {useEffect, useState} from 'react';
import {useLocale} from 'next-intl';
import ProtectedRoute from '@/components/ProtectedRoute';
import {useAuth} from '@/contexts/AuthContext';
import {apiClient} from '@/lib/api/client';
import {Settings, Save} from 'lucide-react';

export default function AdminSettingsPage() {
    const {user} = useAuth();
    const locale = useLocale();

    const [form, setForm] = useState({project_name: '', allow_registration: false});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [msg, setMsg] = useState<string | null>(null);

    useEffect(() => {
        let mounted = true;
        (async () => {
            try {
                const s = await apiClient.getSettings();
                if (mounted) setForm({project_name: s.project_name ?? '', allow_registration: !!s.allow_registration});
            } catch (e: any) {
                setMsg(e?.message || 'Failed to load settings');
            } finally {
                setLoading(false);
            }
        })();
        return () => {
            mounted = false;
        };
    }, []);

    const onSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setMsg(null);
        setSaving(true);
        try {
            await apiClient.updateSettings(form);
            setMsg('Settings saved');
        } catch (e: any) {
            setMsg(e?.message || 'Failed to save settings');
        } finally {
            setSaving(false);
        }
    };

    return (
        <ProtectedRoute>
            <div className="max-w-3xl mx-auto px-4 py-10">
                <div className="mb-8">
                    <h1 className="text-2xl font-bold">Admin settings</h1>
                    <p className="text-gray-600">Rename PlugBot and control registration.</p>
                </div>

                {!user?.is_superuser ? (
                    <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4">
                        You do not have permission to view this page.
                    </div>
                ) : (
                    <div className="bg-white rounded-2xl shadow-sm border p-6">
                        <div className="flex items-center gap-2 mb-4">
                            <Settings className="w-5 h-5"/>
                            <h2 className="font-semibold">General</h2>
                        </div>

                        {msg && (
                            <div
                                className={`mb-4 text-sm rounded-lg px-3 py-2 ${msg.includes('saved') ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                                {msg}
                            </div>
                        )}

                        <form onSubmit={onSubmit} className="space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Project name</label>
                                <input
                                    value={form.project_name}
                                    onChange={(e) => setForm((f) => ({...f, project_name: e.target.value}))}
                                    placeholder="e.g. My Awesome Bot"
                                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                                <p className="text-xs text-gray-500 mt-1">Shown in the navbar and meta.</p>
                            </div>

                            <div className="flex items-center gap-3">
                                <input
                                    id="allow_reg"
                                    type="checkbox"
                                    checked={form.allow_registration}
                                    onChange={(e) => setForm((f) => ({...f, allow_registration: e.target.checked}))}
                                    className="h-4 w-4"
                                />
                                <label htmlFor="allow_reg" className="text-sm text-gray-800">Allow user
                                    registration</label>
                            </div>

                            <button
                                type="submit"
                                disabled={saving}
                                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
                            >
                                <Save className="w-4 h-4"/> Save settings
                            </button>
                        </form>
                    </div>
                )}
            </div>
        </ProtectedRoute>
    );
}

