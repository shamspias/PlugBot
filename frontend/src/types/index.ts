export interface Bot {
    id: string;
    name: string;
    description?: string;
    dify_endpoint: string;
    dify_type: 'chat' | 'agent' | 'chatflow' | 'workflow';
    response_mode: 'streaming' | 'blocking';
    auto_generate_title: boolean;
    enable_file_upload: boolean;
    telegram_markdown_enabled: boolean;
    is_active: boolean;
    is_telegram_connected: boolean;
    telegram_bot_username?: string;
    telegram_bot_token?: string;
    last_health_check?: string;
    health_status: 'healthy' | 'unhealthy' | 'unknown';
    auth_required: boolean;
    allowed_email_domains?: string;
    auth_email_subject_template?: string;
    auth_email_body_template?: string;
    auth_email_html_template?: string;
    created_at: string;
    updated_at?: string;
}

export interface BotCreate {
    name: string;
    description?: string;
    dify_endpoint: string;
    dify_api_key: string;
    dify_type: 'chat' | 'agent' | 'chatflow' | 'workflow';
    telegram_bot_token?: string;
    response_mode: 'streaming' | 'blocking';
    auto_generate_title: boolean;
    enable_file_upload: boolean;
    telegram_markdown_enabled: boolean;
    auth_required: boolean;
    allowed_email_domains?: string;
    auth_email_subject_template?: string;
    auth_email_body_template?: string;
    auth_email_html_template?: string;
}

export interface BotStatus {
    id: string;
    name: string;
    is_active: boolean;
    is_telegram_connected: boolean;
    health_status: string;
    last_health_check?: string;
    is_running: boolean;
    conversation_count: number;
}

export interface Conversation {
    id: string;
    bot_id: string;
    title?: string;
    telegram_chat_id: string;
    telegram_username?: string;
    telegram_chat_type?: string;
    is_active: boolean;
    message_count: number;
    last_message_at?: string;
    created_at: string;
    updated_at?: string;
}