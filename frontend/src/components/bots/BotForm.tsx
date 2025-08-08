import React from 'react';
import {BotCreate} from '@/types';
import {Button} from '@/components/ui/button';
import {Shield, Info} from 'lucide-react';

interface BotFormProps {
    initialData?: Partial<BotCreate>;
    onSubmit: (data: BotCreate) => void;
    onCancel: () => void;
}

interface BotFormState {
    formData: BotCreate;
    showAuthHelp: boolean;
}

export class BotForm extends React.Component<BotFormProps, BotFormState> {
    state: BotFormState = {
        formData: {
            name: '',
            description: '',
            dify_endpoint: '',
            dify_api_key: '',
            dify_type: 'chat',
            telegram_bot_token: '',
            response_mode: 'streaming',
            auto_generate_title: true,
            enable_file_upload: true,
            auth_required: false,
            allowed_email_domains: '',
            ...this.props.initialData,
        },
        showAuthHelp: false,
    };

    handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const {name, value, type} = e.target;
        const checked = (e.target as HTMLInputElement).checked;

        this.setState(prevState => ({
            formData: {
                ...prevState.formData,
                [name]: type === 'checkbox' ? checked : value,
            },
        }));
    };

    handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        this.props.onSubmit(this.state.formData);
    };

    render() {
        const {formData, showAuthHelp} = this.state;
        const {onCancel} = this.props;

        return (
            <form onSubmit={this.handleSubmit} className="space-y-6">
                {/* Basic Information */}
                <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Bot Name *
                        </label>
                        <input
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={this.handleChange}
                            required
                            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            placeholder="My Dify Bot"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Description
                        </label>
                        <textarea
                            name="description"
                            value={formData.description}
                            onChange={this.handleChange}
                            rows={3}
                            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
                            placeholder="A helpful AI assistant powered by Dify"
                        />
                    </div>
                </div>

                {/* Dify Configuration */}
                <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900">Dify Configuration</h3>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Dify Endpoint *
                        </label>
                        <input
                            type="url"
                            name="dify_endpoint"
                            value={formData.dify_endpoint}
                            onChange={this.handleChange}
                            required
                            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            placeholder="http://agents.algolyzerlab.com/v1"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Dify API Key *
                        </label>
                        <input
                            type="password"
                            name="dify_api_key"
                            value={formData.dify_api_key}
                            onChange={this.handleChange}
                            required={!this.props.initialData}
                            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            placeholder="app-xxxxxxxxxxxxx"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Dify Type
                            </label>
                            <select
                                name="dify_type"
                                value={formData.dify_type}
                                onChange={this.handleChange}
                                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            >
                                <option value="chat">Chat</option>
                                <option value="agent">Agent</option>
                                <option value="chatflow">Chatflow</option>
                                <option value="workflow">Workflow</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Response Mode
                            </label>
                            <select
                                name="response_mode"
                                value={formData.response_mode}
                                onChange={this.handleChange}
                                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            >
                                <option value="streaming">Streaming</option>
                                <option value="blocking">Blocking</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Telegram Configuration */}
                <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900">Telegram Configuration</h3>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Telegram Bot Token (Optional)
                        </label>
                        <input
                            type="password"
                            name="telegram_bot_token"
                            value={formData.telegram_bot_token}
                            onChange={this.handleChange}
                            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
                        />
                        <p className="mt-2 text-sm text-gray-500">
                            Get your bot token from @BotFather on Telegram
                        </p>
                    </div>
                </div>

                {/* Advanced Settings */}
                <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900">Advanced Settings</h3>

                    <div className="space-y-3">
                        <label className="flex items-center space-x-3 cursor-pointer">
                            <input
                                type="checkbox"
                                name="auto_generate_title"
                                checked={formData.auto_generate_title}
                                onChange={this.handleChange}
                                className="w-4 h-4 text-blue-600 bg-gray-100 rounded border-gray-300 focus:ring-blue-500"
                            />
                            <span className="text-sm font-medium text-gray-700">
                                Auto-generate conversation titles
                            </span>
                        </label>

                        <label className="flex items-center space-x-3 cursor-pointer">
                            <input
                                type="checkbox"
                                name="enable_file_upload"
                                checked={formData.enable_file_upload}
                                onChange={this.handleChange}
                                className="w-4 h-4 text-blue-600 bg-gray-100 rounded border-gray-300 focus:ring-blue-500"
                            />
                            <span className="text-sm font-medium text-gray-700">
                                Enable file uploads
                            </span>
                        </label>
                    </div>
                </div>

                {/* Authentication Settings */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                            <Shield className="h-5 w-5 text-blue-600"/>
                            Authentication Settings
                        </h3>
                        <button
                            type="button"
                            onClick={() => this.setState({showAuthHelp: !showAuthHelp})}
                            className="text-blue-600 hover:text-blue-700"
                        >
                            <Info className="h-5 w-5"/>
                        </button>
                    </div>

                    {showAuthHelp && (
                        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <p className="text-sm text-blue-800">
                                When authentication is enabled, users must verify their email address before they can
                                use the bot.
                                Only users with email addresses from the specified domains will be allowed to
                                authenticate.
                                Users will receive a verification code via email and must enter it in Telegram to gain
                                access.
                            </p>
                        </div>
                    )}

                    <label className="flex items-center space-x-3 cursor-pointer">
                        <input
                            type="checkbox"
                            name="auth_required"
                            checked={formData.auth_required}
                            onChange={this.handleChange}
                            className="w-4 h-4 text-blue-600 bg-gray-100 rounded border-gray-300 focus:ring-blue-500"
                        />
                        <span className="text-sm font-medium text-gray-700">
                            Require email authentication
                        </span>
                    </label>

                    {formData.auth_required && (
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Allowed Email Domains
                            </label>
                            <input
                                type="text"
                                name="allowed_email_domains"
                                value={formData.allowed_email_domains}
                                onChange={this.handleChange}
                                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                                placeholder="algolyzer.com, google.com"
                            />
                            <p className="mt-2 text-sm text-gray-500">
                                Enter comma-separated domain names (e.g., algolyzer.com, google.com).
                                Only users with email addresses from these domains can authenticate.
                            </p>
                        </div>
                    )}
                </div>

                {/* Actions */}
                <div className="flex justify-end space-x-3 pt-6 border-t">
                    <Button type="button" variant="secondary" onClick={onCancel}>
                        Cancel
                    </Button>
                    <Button type="submit" variant="primary">
                        {this.props.initialData ? 'Update Bot' : 'Create Bot'}
                    </Button>
                </div>
            </form>
        );
    }
}