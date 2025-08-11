import React from 'react';
import {useTranslations} from 'next-intl';

import {Bot, BotStatus} from '@/types';
import {Card, CardContent, CardHeader} from '@/components/ui/card';
import {Button} from '@/components/ui/button';
import {Badge} from '@/components/ui/badge';
import {apiClient} from '@/lib/api/client';
import {
    Bot as BotIcon,
    Play,
    Pause,
    RefreshCw,
    Settings,
    Trash2,
    Activity,
    MessageCircle,
    Link,
} from 'lucide-react';

type T = ReturnType<typeof useTranslations>;

interface BotCardInnerProps {
    bot: Bot;
    onUpdate: () => void;
    onEdit: (bot: Bot) => void;
    onDelete: (bot: Bot) => void;
    t: T;
}

interface BotCardState {
    status: BotStatus | null;
    loading: boolean;
}

// Non-exported inner class: accepts `t`
class BotCardInner extends React.Component<BotCardInnerProps, BotCardState> {
    state: BotCardState = {
        status: null,
        loading: false,
    };

    componentDidMount() {
        this.fetchStatus();
    }

    fetchStatus = async () => {
        try {
            const status = await apiClient.getBotStatus(this.props.bot.id);
            this.setState({status});
        } catch (error) {
            console.error('Failed to fetch bot status:', error);
        }
    };

    handleStart = async () => {
        this.setState({loading: true});
        try {
            await apiClient.startBot(this.props.bot.id);
            await this.fetchStatus();
            this.props.onUpdate();
        } catch (error) {
            console.error('Failed to start bot:', error);
        } finally {
            this.setState({loading: false});
        }
    };

    handleStop = async () => {
        this.setState({loading: true});
        try {
            await apiClient.stopBot(this.props.bot.id);
            await this.fetchStatus();
            this.props.onUpdate();
        } catch (error) {
            console.error('Failed to stop bot:', error);
        } finally {
            this.setState({loading: false});
        }
    };

    handleRestart = async () => {
        this.setState({loading: true});
        try {
            await apiClient.restartBot(this.props.bot.id);
            await this.fetchStatus();
            this.props.onUpdate();
        } catch (error) {
            console.error('Failed to restart bot:', error);
        } finally {
            this.setState({loading: false});
        }
    };

    handleHealth = async () => {
        this.setState({loading: true});
        try {
            await apiClient.healthCheck(this.props.bot.id);
            await this.fetchStatus();
            this.props.onUpdate();
        } catch (error) {
            console.error('Failed to check health:', error);
        } finally {
            this.setState({loading: false});
        }
    };

    render() {
        const {bot, onEdit, onDelete, t} = this.props;
        const {status, loading} = this.state;

        return (
            <Card className="hover:shadow-lg transition-shadow">
                <CardHeader>
                    <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3">
                            <div className="p-2 bg-blue-100 rounded-lg">
                                <BotIcon className="h-6 w-6 text-blue-600"/>
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold">{bot.name}</h3>
                                <p className="text-sm text-gray-500">{bot.description}</p>
                            </div>
                        </div>
                        <div className="flex items-center space-x-2">
                            {bot.is_active ? (
                                <Badge variant="success">{t('common.active')}</Badge>
                            ) : (
                                <Badge variant="default">{t('common.inactive')}</Badge>
                            )}
                            {status?.is_running && <Badge variant="info">{t('common.running')}</Badge>}
                            {!status?.is_running && <Badge variant="default">{t('common.stopped')}</Badge>}
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {/* Bot Info */}
                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <span className="text-gray-500">{t('bots.status.type')}</span>
                                <span className="ml-2 font-medium capitalize">{bot.dify_type}</span>
                            </div>
                            <div>
                                <span className="text-gray-500">{t('bots.status.mode')}</span>
                                <span className="ml-2 font-medium capitalize">{bot.response_mode}</span>
                            </div>
                            <div>
                                <span className="text-gray-500">{t('bots.status.health')}</span>
                                <span className="ml-2">
                  {bot.health_status === 'healthy' ? (
                      <Badge variant="success">{t('common.healthy', {default: 'Healthy'})}</Badge>
                  ) : bot.health_status === 'unhealthy' ? (
                      <Badge variant="danger">{t('common.unhealthy', {default: 'Unhealthy'})}</Badge>
                  ) : (
                      <Badge variant="default">{t('common.unknown', {default: 'Unknown'})}</Badge>
                  )}
                </span>
                            </div>
                            <div>
                <span
                    className="text-gray-500"
                    title="Counts unique Telegram threads for this bot. Use /new or /clear to start a fresh thread or when a new user chats."
                >
                  {t('bots.status.conversations')}
                </span>
                                <span className="ml-2 font-medium">{status?.conversation_count || 0}</span>
                            </div>
                        </div>

                        {/* Connection Status */}
                        <div className="flex items-center space-x-4 pt-2 border-t">
                            <div className="flex items-center space-x-2">
                                <Link className="h-4 w-4 text-gray-400"/>
                                <span className="text-sm">
                  {t('bots.status.difyConnection')}:
                  <span
                      className={`ml-1 font-medium ${
                          bot.health_status === 'healthy' ? 'text-green-600' : 'text-red-600'
                      }`}
                  >
                    {bot.health_status === 'healthy'
                        ? t('bots.status.connected')
                        : t('bots.status.disconnected')}
                  </span>
                </span>
                            </div>
                            <div className="flex items-center space-x-2">
                                <MessageCircle className="h-4 w-4 text-gray-400"/>
                                <span className="text-sm">
                  Telegram:
                  <span
                      className={`ml-1 font-medium ${
                          bot.is_telegram_connected ? 'text-green-600' : 'text-gray-600'
                      }`}
                  >
                    {bot.is_telegram_connected
                        ? t('bots.status.connected')
                        : t('bots.status.notConfigured')}
                  </span>
                </span>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center justify-between pt-4 border-t">
                            <div className="flex items-center space-x-2">
                                {bot.telegram_bot_token && (
                                    <>
                                        {status?.is_running ? (
                                            <>
                                                <Button
                                                    size="sm"
                                                    variant="secondary"
                                                    onClick={this.handleStop}
                                                    disabled={loading}
                                                >
                                                    <Pause className="h-4 w-4 mr-1"/>
                                                    {t('bots.actions.stop')}
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant="secondary"
                                                    onClick={this.handleRestart}
                                                    disabled={loading}
                                                >
                                                    <RefreshCw className="h-4 w-4 mr-1"/>
                                                    {t('bots.actions.restart')}
                                                </Button>
                                            </>
                                        ) : (
                                            <Button
                                                size="sm"
                                                variant="success"
                                                onClick={this.handleStart}
                                                disabled={loading}
                                            >
                                                <Play className="h-4 w-4 mr-1"/>
                                                {t('bots.actions.start')}
                                            </Button>
                                        )}
                                    </>
                                )}
                                <Button
                                    size="sm"
                                    variant="secondary"
                                    onClick={this.handleHealth}
                                    disabled={loading}
                                >
                                    <Activity className="h-4 w-4 mr-1"/>
                                    {t('bots.actions.checkHealth')}
                                </Button>
                            </div>
                            <div className="flex items-center space-x-2">
                                <Button size="sm" variant="secondary" onClick={() => onEdit(bot)}>
                                    <Settings className="h-4 w-4"/>
                                </Button>
                                <Button size="sm" variant="danger" onClick={() => onDelete(bot)}>
                                    <Trash2 className="h-4 w-4"/>
                                </Button>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        );
    }
}

// Tiny wrapper: keeps the export name and provides `t`
export function BotCard(
    props: Omit<React.ComponentProps<typeof BotCardInner>, 't'>
) {
    const t = useTranslations(); // root; use t('common.*') and t('bots.*')
    return <BotCardInner {...props} t={t}/>;
}
