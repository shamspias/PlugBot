import React from 'react';
import {render, screen, waitFor} from '@testing-library/react';
import {BotCard} from '@/components/bots/BotCard';
import {apiClient} from '@/lib/api/client';
import {Bot} from '@/types';

jest.mock('@/lib/api/client', () => ({
    apiClient: {
        getBotStatus: jest.fn().mockResolvedValue({
            id: 'b1',
            name: 'Test',
            is_active: true,
            is_telegram_connected: true,
            health_status: 'healthy',
            last_health_check: new Date().toISOString(),
            is_running: true,
            conversation_count: 1,
        }),
        startBot: jest.fn(),
        stopBot: jest.fn(),
        restartBot: jest.fn(),
        healthCheck: jest.fn(),
    },
}));

const bot: Bot = {
    id: 'b1',
    name: 'Test Bot',
    description: 'desc',
    dify_endpoint: 'http://localhost:1234/v1',
    dify_type: 'chat',
    response_mode: 'streaming',
    max_tokens: 2000,
    temperature: 7,
    auto_generate_title: true,
    enable_file_upload: true,
    is_active: true,
    is_telegram_connected: true,
    health_status: 'healthy',
    created_at: new Date().toISOString(),
    telegram_bot_username: 'test_bot',
};

describe('BotCard conversations label', () => {
    it('shows Conversations (unique chats) with count', async () => {
        render(
            <BotCard
                bot={bot}
                onUpdate={() => {
                }}
                onEdit={() => {
                }}
                onDelete={() => {
                }}
            />
        );

        await waitFor(() =>
            expect((apiClient.getBotStatus as jest.Mock)).toHaveBeenCalled()
        );

        expect(
            screen.getByText(/Conversations \(unique chats\):/i)
        ).toBeInTheDocument();
        expect(screen.getByText('1')).toBeInTheDocument();
    });
});
