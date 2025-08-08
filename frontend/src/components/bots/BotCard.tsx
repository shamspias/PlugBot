import React from 'react';
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

interface BotCardProps {
    bot: Bot;
    onUpdate: () => void;
    onEdit: (bot: Bot) => void;
    onDelete: (bot: Bot) => void;
}

interface BotCardState {
    status: BotStatus | null;
    loading: boolean;
}

export class BotCard extends React.Component<BotCardProps, BotCardState> {
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

    handleHealthCheck = async () => {
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
        const {bot, onEdit, onDelete} = this.props;
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
                                <Badge variant="success">Active</Badge>
                            ) : (
                                <Badge variant="default">Inactive</Badge>
                            )}
                            {status?.is_running && <Badge variant="info">Running</Badge>}
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {/* Bot Info */}
                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <span className="text-gray-500">Type:</span>
                                <span className="ml-2 font-medium capitalize">{bot.dify_type}</span>
                            </div>
                            <div>
                                <span className="text-gray-500">Mode:</span>
                                <span className="ml-2 font-medium capitalize">{bot.response_mode}</span>
                            </div>
                            <div>
                                <span className="text-gray-500">Health:</span>
                                <span className="ml-2">
                  {bot.health_status === 'healthy' ? (
                      <Badge variant="success">Healthy</Badge>
                  ) : bot.health_status === 'unhealthy' ? (
                      <Badge variant="danger">Unhealthy</Badge>
                  ) : (
                      <Badge variant="default">Unknown</Badge>
                  )}
                </span>
                            </div>
                            <div>
                <span
                    className="text-gray-500"
                    title="Counts unique Telegram threads for this bot. Use /new or /clear to start a fresh thread or when a new user chats."
                >
                  Conversations (unique chats):
                </span>
                                <span className="ml-2 font-medium">{status?.conversation_count || 0}</span>
                            </div>
                        </div>

                        {/* Connection Status */}
                        <div className="flex items-center space-x-4 pt-2 border-t">
                            <div className="flex items-center space-x-2">
                                <Link className="h-4 w-4 text-gray-400"/>
                                <span className="text-sm">
                  Dify:
                  <span
                      className={`ml-1 font-medium ${
                          bot.health_status === 'healthy' ? 'text-green-600' : 'text-red-600'
                      }`}
                  >
                    {bot.health_status === 'healthy' ? 'Connected' : 'Disconnected'}
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
                    {bot.is_telegram_connected ? 'Connected' : 'Not configured'}
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
                                                    Stop
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant="secondary"
                                                    onClick={this.handleRestart}
                                                    disabled={loading}
                                                >
                                                    <RefreshCw className="h-4 w-4 mr-1"/>
                                                    Restart
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
                                                Start
                                            </Button>
                                        )}
                                    </>
                                )}
                                <Button
                                    size="sm"
                                    variant="secondary"
                                    onClick={this.handleHealthCheck}
                                    disabled={loading}
                                >
                                    <Activity className="h-4 w-4 mr-1"/>
                                    Check Health
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
