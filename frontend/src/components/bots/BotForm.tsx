import React from 'react';
import {BotCreate} from '@/types';
import {Button} from '@/components/ui/button';

interface BotFormProps {
    initialData?: Partial<BotCreate>;
    onSubmit: (data: BotCreate) => void;
    onCancel: () => void;
}

interface BotFormState {
    formData: BotCreate;
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
            max_tokens: 2000,
            temperature: 7,
            auto_generate_title: true,
            enable_file_upload: true,
            ...this.props.initialData,
        },
    };

    handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const {name, value, type} = e.target;
        const checked = (e.target as HTMLInputElement).checked;

        this.setState(prevState => ({
            formData: {
                ...prevState.formData,
                [name]: type === 'checkbox' ? checked :
                    type === 'number' ? parseInt(value) : value,
            },
        }));
    };

    handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        this.props.onSubmit(this.state.formData);
    };

    render() {
        const {formData} = this.state;
        const {onCancel} = this.props;

        return (
            <form onSubmit={this.handleSubmit} className="space-y-6">
                {/* Basic Information */}
                <div className="space-y-4">
                    <h3 className="text-lg font-medium">Basic Information</h3>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Bot Name *
                        </label>
                        <input
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={this.handleChange}
                            required
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="My Dify Bot"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Description
                        </label>
                        <textarea
                            name="description"
                            value={formData.description}
                            onChange={this.handleChange}
                            rows={3}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="A helpful AI assistant powered by Dify"
                        />
                    </div>
                </div>

                {/* Dify Configuration */}
                <div className="space-y-4">
                    <h3 className="text-lg font-medium">Dify Configuration</h3>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Dify Endpoint *
                        </label>
                        <input
                            type="url"
                            name="dify_endpoint"
                            value={formData.dify_endpoint}
                            onChange={this.handleChange}
                            required
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="http://agents.algolyzerlab.com/v1"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Dify API Key *
                        </label>
                        <input
                            type="password"
                            name="dify_api_key"
                            value={formData.dify_api_key}
                            onChange={this.handleChange}
                            required={!this.props.initialData}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="app-xxxxxxxxxxxxx"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Dify Type
                            </label>
                            <select
                                name="dify_type"
                                value={formData.dify_type}
                                onChange={this.handleChange}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="chat">Chat</option>
                                <option value="agent">Agent</option>
                                <option value="chatflow">Chatflow</option>
                                <option value="workflow">Workflow</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Response Mode
                            </label>
                            <select
                                name="response_mode"
                                value={formData.response_mode}
                                onChange={this.handleChange}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="streaming">Streaming</option>
                                <option value="blocking">Blocking</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Telegram Configuration */}
                <div className="space-y-4">
                    <h3 className="text-lg font-medium">Telegram Configuration</h3>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Telegram Bot Token (Optional)
                        </label>
                        <input
                            type="password"
                            name="telegram_bot_token"
                            value={formData.telegram_bot_token}
                            onChange={this.handleChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
                        />
                        <p className="mt-1 text-sm text-gray-500">
                            Get your bot token from @BotFather on Telegram
                        </p>
                    </div>
                </div>

                {/* Advanced Settings */}
                <div className="space-y-4">
                    <h3 className="text-lg font-medium">Advanced Settings</h3>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Max Tokens
                            </label>
                            <input
                                type="number"
                                name="max_tokens"
                                value={formData.max_tokens}
                                onChange={this.handleChange}
                                min={100}
                                max={10000}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Temperature (0-10)
                            </label>
                            <input
                                type="number"
                                name="temperature"
                                value={formData.temperature}
                                onChange={this.handleChange}
                                min={0}
                                max={10}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                name="auto_generate_title"
                                checked={formData.auto_generate_title}
                                onChange={this.handleChange}
                                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <span className="text-sm font-medium text-gray-700">
                Auto-generate conversation titles
              </span>
                        </label>

                        <label className="flex items-center space-x-2">
                            <input
                                type="checkbox"
                                name="enable_file_upload"
                                checked={formData.enable_file_upload}
                                onChange={this.handleChange}
                                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <span className="text-sm font-medium text-gray-700">
                Enable file uploads
              </span>
                        </label>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end space-x-3 pt-4 border-t">
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