import {Bot, BotCreate, BotStatus, Conversation} from '@/types';

class ApiClient {
    private baseUrl: string;

    constructor() {
        this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8531/api/v1';
    }

    private async request<T>(
        endpoint: string,
        options?: RequestInit
    ): Promise<T> {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options?.headers,
            },
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({detail: 'Unknown error'}));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        if (response.status === 204) {
            return {} as T;
        }

        return response.json();
    }

    // Bot endpoints
    async getBots(): Promise<Bot[]> {
        return this.request<Bot[]>('/bots');
    }

    async getBot(id: string): Promise<Bot> {
        return this.request<Bot>(`/bots/${id}`);
    }

    async getBotStatus(id: string): Promise<BotStatus> {
        return this.request<BotStatus>(`/bots/${id}/status`);
    }

    async createBot(data: BotCreate): Promise<Bot> {
        return this.request<Bot>('/bots', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateBot(id: string, data: Partial<BotCreate>): Promise<Bot> {
        return this.request<Bot>(`/bots/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    async deleteBot(id: string): Promise<void> {
        return this.request<void>(`/bots/${id}`, {
            method: 'DELETE',
        });
    }

    async startBot(id: string): Promise<{ message: string }> {
        return this.request<{ message: string }>(`/bots/${id}/start`, {
            method: 'POST',
        });
    }

    async stopBot(id: string): Promise<{ message: string }> {
        return this.request<{ message: string }>(`/bots/${id}/stop`, {
            method: 'POST',
        });
    }

    async restartBot(id: string): Promise<{ message: string }> {
        return this.request<{ message: string }>(`/bots/${id}/restart`, {
            method: 'POST',
        });
    }

    async healthCheck(id: string): Promise<any> {
        return this.request<any>(`/bots/${id}/health-check`, {
            method: 'POST',
        });
    }

    // Conversation endpoints
    async getConversations(botId?: string): Promise<Conversation[]> {
        const params = botId ? `?bot_id=${botId}` : '';
        return this.request<Conversation[]>(`/conversations${params}`);
    }
}

export const apiClient = new ApiClient();
