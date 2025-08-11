'use client';

import React from 'react';
import {Bot, BotCreate} from '@/types';
import {apiClient} from '@/lib/api/client';
import {BotCard} from '@/components/bots/BotCard';
import {BotForm} from '@/components/bots/BotForm';
import {Modal} from '@/components/ui/modal';
import {Button} from '@/components/ui/button';
import {Plus, RefreshCw, Bot as BotIcon} from 'lucide-react';
import ProtectedRoute from '@/components/ProtectedRoute';

// ADD: next-intl
import {useTranslations} from 'next-intl';

type T = ReturnType<typeof useTranslations>;

interface AppState {
    bots: Bot[];
    loading: boolean;
    error: string | null;
    showCreateModal: boolean;
    showEditModal: boolean;
    editingBot: Bot | null;
    showDeleteConfirm: boolean;
    deletingBot: Bot | null;
}

// CHANGE: class accepts `t` prop
class DashboardInner extends React.Component<{ t: T }, AppState> {
    state: AppState = {
        bots: [],
        loading: true,
        error: null,
        showCreateModal: false,
        showEditModal: false,
        editingBot: null,
        showDeleteConfirm: false,
        deletingBot: null,
    };

    componentDidMount() {
        this.fetchBots();
    }

    fetchBots = async () => {
        this.setState({loading: true, error: null});
        try {
            const bots = await apiClient.getBots();
            this.setState({bots, loading: false});
        } catch (error) {
            this.setState({
                error:
                    error instanceof Error
                        ? error.message
                        : this.props.t('errors.fetchFailed'),
                loading: false,
            });
        }
    };

    handleCreateBot = async (data: BotCreate) => {
        try {
            await apiClient.createBot(data);
            this.setState({showCreateModal: false});
            await this.fetchBots();
        } catch (error) {
            alert(
                error instanceof Error
                    ? error.message
                    : this.props.t('errors.createFailed'),
            );
        }
    };

    handleUpdateBot = async (data: BotCreate) => {
        if (!this.state.editingBot) return;

        try {
            await apiClient.updateBot(this.state.editingBot.id, data);
            this.setState({showEditModal: false, editingBot: null});
            await this.fetchBots();
        } catch (error) {
            alert(
                error instanceof Error
                    ? error.message
                    : this.props.t('errors.updateFailed'),
            );
        }
    };

    handleDeleteBot = async () => {
        if (!this.state.deletingBot) return;

        try {
            await apiClient.deleteBot(this.state.deletingBot.id);
            this.setState({showDeleteConfirm: false, deletingBot: null});
            await this.fetchBots();
        } catch (error) {
            alert(
                error instanceof Error
                    ? error.message
                    : this.props.t('errors.deleteFailed'),
            );
        }
    };

    render() {
        const {t} = this.props;
        const {
            bots,
            loading,
            error,
            showCreateModal,
            showEditModal,
            editingBot,
            showDeleteConfirm,
            deletingBot,
        } = this.state;

        return (
            <ProtectedRoute>
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    {/* Header */}
                    <div className="mb-8">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-3xl font-bold text-gray-900">
                                    {t('header.title')}
                                </h2>
                                <p className="mt-2 text-gray-600">{t('header.description')}</p>
                            </div>
                            <div className="flex items-center space-x-3">
                                <Button
                                    variant="secondary"
                                    onClick={this.fetchBots}
                                    disabled={loading}
                                >
                                    <RefreshCw
                                        className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`}
                                    />
                                    {t('actions.refresh')}
                                </Button>
                                <Button
                                    variant="primary"
                                    onClick={() => this.setState({showCreateModal: true})}
                                >
                                    <Plus className="h-4 w-4 mr-2"/>
                                    {t('actions.add')}
                                </Button>
                            </div>
                        </div>
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                            <p className="text-red-700">{error}</p>
                        </div>
                    )}

                    {/* Bot Grid */}
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="text-center">
                                <RefreshCw className="h-8 w-8 animate-spin text-gray-400 mx-auto mb-4"/>
                                <p className="text-gray-500">{t('loading')}</p>
                            </div>
                        </div>
                    ) : bots.length === 0 ? (
                        <div className="text-center py-12 bg-white rounded-lg border-2 border-dashed border-gray-300">
                            <BotIcon className="h-12 w-12 text-gray-400 mx-auto mb-4"/>
                            <h3 className="text-lg font-medium text-gray-900 mb-2">
                                {t('noBots')}
                            </h3>
                            <p className="text-gray-500 mb-6">{t('noBotsDescription')}</p>
                            <Button
                                variant="primary"
                                onClick={() => this.setState({showCreateModal: true})}
                            >
                                <Plus className="h-4 w-4 mr-2"/>
                                {t('addFirstBot')}
                            </Button>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {bots.map((bot) => (
                                <BotCard
                                    key={bot.id}
                                    bot={bot}
                                    onUpdate={this.fetchBots}
                                    onEdit={(bot) =>
                                        this.setState({editingBot: bot, showEditModal: true})
                                    }
                                    onDelete={(bot) =>
                                        this.setState({
                                            deletingBot: bot,
                                            showDeleteConfirm: true,
                                        })
                                    }
                                />
                            ))}
                        </div>
                    )}

                    {/* Create Modal */}
                    <Modal
                        isOpen={showCreateModal}
                        onClose={() => this.setState({showCreateModal: false})}
                        title={t('form.createTitle')}
                    >
                        <BotForm
                            onSubmit={this.handleCreateBot}
                            onCancel={() => this.setState({showCreateModal: false})}
                        />
                    </Modal>

                    {/* Edit Modal */}
                    <Modal
                        isOpen={showEditModal}
                        onClose={() =>
                            this.setState({showEditModal: false, editingBot: null})
                        }
                        title={t('form.editTitle')}
                    >
                        {editingBot && (
                            <BotForm
                                initialData={editingBot}
                                onSubmit={this.handleUpdateBot}
                                onCancel={() =>
                                    this.setState({showEditModal: false, editingBot: null})
                                }
                            />
                        )}
                    </Modal>

                    {/* Delete Confirmation Modal */}
                    <Modal
                        isOpen={showDeleteConfirm}
                        onClose={() =>
                            this.setState({showDeleteConfirm: false, deletingBot: null})
                        }
                        title={t('deleteConfirm.title')}
                    >
                        <div className="space-y-4">
                            <p className="text-gray-700">
                                {t('deleteConfirm.message', {
                                    name: deletingBot?.name ?? '',
                                })}
                            </p>
                            <div className="flex justify-end space-x-3">
                                <Button
                                    variant="secondary"
                                    onClick={() =>
                                        this.setState({
                                            showDeleteConfirm: false,
                                            deletingBot: null,
                                        })
                                    }
                                >
                                    {t('deleteConfirm.cancel')}
                                </Button>
                                <Button variant="danger" onClick={this.handleDeleteBot}>
                                    {t('deleteConfirm.delete')}
                                </Button>
                            </div>
                        </div>
                    </Modal>
                </div>
            </ProtectedRoute>
        );
    }
}

// REPLACE default export with wrapper that injects `t` for next-intl
export default function DashboardPage() {
    const t = useTranslations('bots');
    return <DashboardInner t={t}/>;
}
