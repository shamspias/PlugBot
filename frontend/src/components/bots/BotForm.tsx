import React from 'react';
import {useTranslations} from 'next-intl';
import {BotCreate} from '@/types';
import {Button} from '@/components/ui/button';
import {Shield, Info, Mail, Code} from 'lucide-react';

type T = ReturnType<typeof useTranslations>;

interface BotFormInnerProps {
    initialData?: Partial<BotCreate>;
    onSubmit: (data: BotCreate) => void;
    onCancel: () => void;
    t: T;
}

interface BotFormState {
    formData: BotCreate;
    showAuthHelp: boolean;
    showEmailTemplateHelp: boolean;
    emailTemplateTab: 'subject' | 'body' | 'html';
}

// Keys that are booleans in BotCreate
const BOOLEAN_KEYS = new Set<keyof BotCreate>([
    'auto_generate_title',
    'enable_file_upload',
    'auth_required',
    'telegram_markdown_enabled',
]);

// Narrowed literal unions for select fields
type DifyType = BotCreate['dify_type'];
type ResponseMode = BotCreate['response_mode'];

class BotFormInner extends React.Component<BotFormInnerProps, BotFormState> {
    constructor(props: BotFormInnerProps) {
        super(props);

        const defaults: BotCreate = {
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
            telegram_markdown_enabled: false,
            auth_email_subject_template: '',
            auth_email_body_template: '',
            auth_email_html_template: '',
        };

        const incoming = props.initialData ?? {};
        const merged: BotCreate = {...defaults, ...incoming};

        // ensure booleans are never undefined
        merged.auto_generate_title =
            incoming.auto_generate_title ?? defaults.auto_generate_title;
        merged.enable_file_upload =
            incoming.enable_file_upload ?? defaults.enable_file_upload;
        merged.auth_required = incoming.auth_required ?? defaults.auth_required;
        merged.telegram_markdown_enabled =
            incoming.telegram_markdown_enabled ?? defaults.telegram_markdown_enabled;

        this.state = {
            formData: merged,
            showAuthHelp: false,
            showEmailTemplateHelp: false,
            emailTemplateTab: 'body',
        };
    }

    handleChange = (
        e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
    ) => {
        const target = e.target as HTMLInputElement;
        const name = target.name as keyof BotCreate;

        let nextValue: BotCreate[typeof name];

        if (BOOLEAN_KEYS.has(name)) {
            nextValue = (target.type === 'checkbox'
                ? target.checked
                : target.value === 'true') as BotCreate[typeof name];
        } else if (name === 'dify_type') {
            nextValue = target.value as DifyType as BotCreate[typeof name];
        } else if (name === 'response_mode') {
            nextValue = target.value as ResponseMode as BotCreate[typeof name];
        } else {
            nextValue = target.value as BotCreate[typeof name];
        }

        this.setState((prev) => ({
            ...prev,
            formData: {
                ...prev.formData,
                [name]: nextValue,
            },
        }));
    };

    handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        const clean = (s?: string) => (s ?? '').trim();

        const payload: BotCreate = {
            ...this.state.formData,
            name: clean(this.state.formData.name),
            description: clean(this.state.formData.description),
            dify_endpoint: clean(this.state.formData.dify_endpoint),
            dify_api_key: clean(this.state.formData.dify_api_key),
            telegram_bot_token: clean(this.state.formData.telegram_bot_token),
            allowed_email_domains: clean(this.state.formData.allowed_email_domains),
            auth_email_subject_template: clean(this.state.formData.auth_email_subject_template),
            auth_email_body_template: clean(this.state.formData.auth_email_body_template),
            auth_email_html_template: clean(this.state.formData.auth_email_html_template),
        };

        this.props.onSubmit(payload);
    };

    render() {
        const {formData, showAuthHelp, showEmailTemplateHelp, emailTemplateTab} = this.state;
        const {onCancel, t} = this.props;

        return (
            <form onSubmit={this.handleSubmit} className="space-y-6">
                {/* Basic Information */}
                <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900">
                        {t('form.sections.basic')}
                    </h3>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            {t('form.fields.name')} *
                        </label>
                        <input
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={this.handleChange}
                            required
                            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            placeholder={t('form.fields.namePlaceholder')}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            {t('form.fields.description')}
                        </label>
                        <textarea
                            name="description"
                            value={formData.description}
                            onChange={this.handleChange}
                            rows={3}
                            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
                            placeholder={t('form.fields.descriptionPlaceholder')}
                        />
                    </div>
                </div>

                {/* Dify Configuration */}
                <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900">
                        {t('form.sections.dify')}
                    </h3>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            {t('form.fields.difyEndpoint')} *
                        </label>
                        <input
                            type="url"
                            name="dify_endpoint"
                            value={formData.dify_endpoint}
                            onChange={this.handleChange}
                            required
                            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            placeholder={t('form.fields.difyEndpointPlaceholder')}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            {t('form.fields.difyApiKey')} *
                        </label>
                        <input
                            type="password"
                            name="dify_api_key"
                            value={formData.dify_api_key}
                            onChange={this.handleChange}
                            required={!this.props.initialData}
                            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            placeholder={t('form.fields.difyApiKeyPlaceholder')}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                {t('form.fields.difyType')}
                            </label>
                            <select
                                name="dify_type"
                                value={formData.dify_type}
                                onChange={this.handleChange}
                                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            >
                                <option value="chat">{t('form.options.difyType.chat')}</option>
                                <option value="agent">{t('form.options.difyType.agent')}</option>
                                <option value="chatflow">{t('form.options.difyType.chatflow')}</option>
                                <option value="workflow">{t('form.options.difyType.workflow')}</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                {t('form.fields.responseMode')}
                            </label>
                            <select
                                name="response_mode"
                                value={formData.response_mode}
                                onChange={this.handleChange}
                                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            >
                                <option value="streaming">
                                    {t('form.options.responseMode.streaming')}
                                </option>
                                <option value="blocking">
                                    {t('form.options.responseMode.blocking')}
                                </option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Telegram Configuration */}
                <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-gray-900">
                        {t('form.sections.telegram')}
                    </h3>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            {t('form.fields.telegramToken')}
                        </label>
                        <input
                            type="password"
                            name="telegram_bot_token"
                            value={formData.telegram_bot_token}
                            onChange={this.handleChange}
                            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            placeholder={t('form.fields.telegramTokenPlaceholder')}
                        />
                        <p className="mt-2 text-sm text-gray-500">
                            {t('form.fields.telegramTokenHelp')}
                        </p>
                    </div>
                </div>

                {/* Advanced Settings */}
                <div className="space-y-3">
                    <label className="flex items-center space-x-3 cursor-pointer">
                        <input
                            type="checkbox"
                            name="auto_generate_title"
                            checked={!!formData.auto_generate_title}
                            onChange={this.handleChange}
                            className="w-4 h-4 text-blue-600 bg-gray-100 rounded border-gray-300 focus:ring-blue-500"
                        />
                        <span className="text-sm font-medium text-gray-700">
              {t('form.fields.autoGenerateTitle')}
            </span>
                    </label>

                    <label className="flex items-center space-x-3 cursor-pointer">
                        <input
                            type="checkbox"
                            name="enable_file_upload"
                            checked={!!formData.enable_file_upload}
                            onChange={this.handleChange}
                            className="w-4 h-4 text-blue-600 bg-gray-100 rounded border-gray-300 focus:ring-blue-500"
                        />
                        <span className="text-sm font-medium text-gray-700">
              {t('form.fields.enableFileUpload')}
            </span>
                    </label>

                    <label className="flex items-center space-x-3 cursor-pointer">
                        <input
                            type="checkbox"
                            name="telegram_markdown_enabled"
                            checked={!!formData.telegram_markdown_enabled}
                            onChange={this.handleChange}
                            className="w-4 h-4 text-blue-600 bg-gray-100 rounded border-gray-300 focus:ring-blue-500"
                        />
                        <span className="text-sm font-medium text-gray-700">
              {t('form.fields.telegramMarkdown')}
            </span>
                    </label>
                </div>

                {/* Authentication Settings */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                            <Shield className="h-5 w-5 text-blue-600"/>
                            {t('form.sections.auth')}
                        </h3>
                        <button
                            type="button"
                            onClick={() => this.setState({showAuthHelp: !showAuthHelp})}
                            className="text-blue-600 hover:text-blue-700"
                            aria-label={t('form.actions.toggleAuthHelp')}
                        >
                            <Info className="h-5 w-5"/>
                        </button>
                    </div>

                    {showAuthHelp && (
                        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <p className="text-sm text-blue-800">{t('form.authHelp')}</p>
                        </div>
                    )}

                    <label className="flex items-center space-x-3 cursor-pointer">
                        <input
                            type="checkbox"
                            name="auth_required"
                            checked={!!formData.auth_required}
                            onChange={this.handleChange}
                            className="w-4 h-4 text-blue-600 bg-gray-100 rounded border-gray-300 focus:ring-blue-500"
                        />
                        <span className="text-sm font-medium text-gray-700">
              {t('form.fields.authRequired')}
            </span>
                    </label>

                    {formData.auth_required && (
                        <>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    {t('form.fields.allowedDomains')}
                                </label>
                                <input
                                    type="text"
                                    name="allowed_email_domains"
                                    value={formData.allowed_email_domains}
                                    onChange={this.handleChange}
                                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                                    placeholder={t('form.fields.allowedDomainsPlaceholder')}
                                />
                                <p className="mt-2 text-sm text-gray-500">
                                    {t('form.fields.allowedDomainsHelp')}
                                </p>
                            </div>

                            {/* Email Template Settings (NEW) */}
                            <div className="border-t pt-4">
                                <div className="flex items-center justify-between mb-4">
                                    <h4 className="text-md font-medium text-gray-900 flex items-center gap-2">
                                        <Mail className="h-4 w-4 text-purple-600"/>
                                        Custom Email Templates
                                    </h4>
                                    <button
                                        type="button"
                                        onClick={() => this.setState({showEmailTemplateHelp: !showEmailTemplateHelp})}
                                        className="text-purple-600 hover:text-purple-700"
                                    >
                                        <Info className="h-4 w-4"/>
                                    </button>
                                </div>

                                {showEmailTemplateHelp && (
                                    <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg mb-4">
                                        <p className="text-sm text-purple-800 mb-2">
                                            Customize the email sent to users for authentication. Available
                                            placeholders:
                                        </p>
                                        <ul className="text-sm text-purple-700 space-y-1">
                                            <li>• <code className="bg-purple-100 px-1 rounded">{'{code}'}</code> - The
                                                6-digit verification code (required in body)
                                            </li>
                                            <li>• <code className="bg-purple-100 px-1 rounded">{'{bot_name}'}</code> -
                                                The name of your bot
                                            </li>
                                        </ul>
                                        <p className="text-sm text-purple-700 mt-2">
                                            Leave empty to use default templates.
                                        </p>
                                    </div>
                                )}

                                {/* Tab selector */}
                                <div className="flex space-x-2 mb-4">
                                    <button
                                        type="button"
                                        onClick={() => this.setState({emailTemplateTab: 'subject'})}
                                        className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                                            emailTemplateTab === 'subject'
                                                ? 'bg-purple-600 text-white'
                                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                        }`}
                                    >
                                        Subject
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => this.setState({emailTemplateTab: 'body'})}
                                        className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                                            emailTemplateTab === 'body'
                                                ? 'bg-purple-600 text-white'
                                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                        }`}
                                    >
                                        Text Body
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => this.setState({emailTemplateTab: 'html'})}
                                        className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                                            emailTemplateTab === 'html'
                                                ? 'bg-purple-600 text-white'
                                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                        }`}
                                    >
                                        HTML Body
                                    </button>
                                </div>

                                {/* Template editors */}
                                {emailTemplateTab === 'subject' && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Email Subject Template
                                        </label>
                                        <input
                                            type="text"
                                            name="auth_email_subject_template"
                                            value={formData.auth_email_subject_template || ''}
                                            onChange={this.handleChange}
                                            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all font-mono text-sm"
                                            placeholder="Your {bot_name} verification code"
                                        />
                                    </div>
                                )}

                                {emailTemplateTab === 'body' && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Email Text Body Template
                                        </label>
                                        <textarea
                                            name="auth_email_body_template"
                                            value={formData.auth_email_body_template || ''}
                                            onChange={this.handleChange}
                                            rows={6}
                                            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all resize-none font-mono text-sm"
                                            placeholder={`Для завершения авторизации в Telegram-боте необходимо подтвердить ваш адрес электронной почты.

Код подтверждения: {code}

Срок действия кода — 5 минут.`}
                                        />
                                    </div>
                                )}

                                {emailTemplateTab === 'html' && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Email HTML Body Template (optional)
                                        </label>
                                        <div className="relative">
                                            <Code className="absolute left-3 top-3 w-4 h-4 text-gray-400"/>
                                            <textarea
                                                name="auth_email_html_template"
                                                value={formData.auth_email_html_template || ''}
                                                onChange={this.handleChange}
                                                rows={10}
                                                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all resize-none font-mono text-xs"
                                                placeholder={`<html>
<body style="font-family: Arial, sans-serif;">
    <h2>{bot_name} - Verification Code</h2>
    <p>Your verification code is:</p>
    <h1 style="color: #667eea; letter-spacing: 3px;">{code}</h1>
    <p>This code expires in 5 minutes.</p>
</body>
</html>`}
                                            />
                                        </div>
                                        <p className="mt-2 text-xs text-gray-500">
                                            HTML template for rich email formatting. Leave empty to use plain text only.
                                        </p>
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </div>

                {/* Actions */}
                <div className="flex justify-end space-x-3 pt-6 border-t">
                    <Button type="button" variant="secondary" onClick={onCancel}>
                        {t('form.buttons.cancel')}
                    </Button>
                    <Button type="submit" variant="primary">
                        {this.props.initialData ? t('form.buttons.update') : t('form.buttons.create')}
                    </Button>
                </div>
            </form>
        );
    }
}

// Wrapper to inject translations
export function BotForm(
    props: Omit<React.ComponentProps<typeof BotFormInner>, 't'>
) {
    const t = useTranslations('bots');
    return <BotFormInner {...props} t={t}/>;
}