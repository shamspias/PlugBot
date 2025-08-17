// Common unions
export type DifyType = 'chat' | 'agent' | 'chatflow' | 'workflow';
export type ResponseMode = 'streaming' | 'blocking';
export type HealthStatus = 'healthy' | 'unhealthy' | 'unknown';
export type ConversationPlatform = 'telegram' | 'discord';

export interface Bot {
    id: string;
    name: string;
    description?: string;

    // Dify config
    dify_endpoint: string;
    dify_type: DifyType;
    response_mode: ResponseMode;
    auto_generate_title: boolean;
    enable_file_upload: boolean;

    // Telegram
    telegram_markdown_enabled: boolean;
    is_telegram_connected: boolean;
    telegram_bot_username?: string;
    telegram_bot_token?: string;

    // Discord
    discord_markdown_enabled: boolean;
    is_discord_connected: boolean;
    discord_bot_username?: string;
    discord_bot_token?: string;
    discord_bot_id?: string;

    // Ops / auth
    is_active: boolean;
    last_health_check?: string;
    health_status: HealthStatus;
    auth_required: boolean;
    allowed_email_domains?: string;

    // Timestamps
    created_at: string;
    updated_at?: string;
}

export interface BotCreate {
    // Required
    name: string;
    dify_endpoint: string;
    dify_api_key: string;
    dify_type: DifyType;
    response_mode: ResponseMode;
    auto_generate_title: boolean;
    enable_file_upload: boolean;
    telegram_markdown_enabled: boolean;
    discord_markdown_enabled: boolean;
    auth_required: boolean;

    // Optional
    description?: string;

    // Integrations (optional at creation)
    telegram_bot_token?: string;
    discord_bot_token?: string;

    // Access control
    allowed_email_domains?: string;
}

export interface BotStatus {
    id: string;
    name: string;

    is_active: boolean;

    // Connections
    is_telegram_connected: boolean;
    is_discord_connected: boolean;

    // Health
    health_status: HealthStatus;
    last_health_check?: string;

    // Runtime
    is_running: boolean;

    // Usage
    conversation_count: number;
}

export interface Conversation {
    id: string;
    bot_id: string;
    title?: string;

    // Which platform this conversation belongs to
    platform: ConversationPlatform;

    // Telegram-specific (present when platform === 'telegram')
    telegram_chat_id?: string;
    telegram_username?: string;
    telegram_chat_type?: string; // e.g., "private" | "group" | "supergroup" | "channel"

    // Discord-specific (present when platform === 'discord')
    discord_guild_id?: string;     // absent for DMs
    discord_channel_id?: string;   // channel or DM channel id
    discord_user_id?: string;      // DM user id, or message author
    discord_username?: string;     // display/global username
    discord_channel_type?: string; // e.g., "GUILD_TEXT" | "DM" | "PUBLIC_THREAD" | "PRIVATE_THREAD"

    // Lifecycle / counts
    is_active: boolean;
    message_count: number;
    last_message_at?: string;

    // Timestamps
    created_at: string;
    updated_at?: string;
}
