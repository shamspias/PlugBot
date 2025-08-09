import {Bot, BotCreate, BotStatus, Conversation} from '@/types';

class ApiClient {
    private baseUrl: string;

    constructor() {
        this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8531/api/v1';
    }

    private getAuthHeaders(): HeadersInit {
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
        return {
            'Content-Type': 'application/json',
            ...(token ? {Authorization: `Bearer ${token}`} : {}),
        };
    }

    private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
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

    // ===== Auth endpoints =====
    async login(email: string, password: string): Promise<any> {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({email, password}),
            headers: this.getAuthHeaders(),
        });
    }

    async register(data: any): Promise<any> {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data),
            headers: this.getAuthHeaders(),
        });
    }

    async logout(): Promise<void> {
        return this.request('/auth/logout', {
            method: 'POST',
            headers: this.getAuthHeaders(),
        });
    }

    async getCurrentUser(): Promise<any> {
        return this.request('/auth/me', {
            headers: this.getAuthHeaders(),
        });
    }

    async refreshAccessToken(refreshToken: string): Promise<any> {
        return this.request('/auth/refresh', {
            method: 'POST',
            body: JSON.stringify({refresh_token: refreshToken}),
            headers: this.getAuthHeaders(),
        });
    }

    async requestPasswordReset(email: string): Promise<any> {
        return this.request('/auth/forgot-password', {
            method: 'POST',
            body: JSON.stringify({email}),
            headers: this.getAuthHeaders(),
        });
    }

    // ===== Bot endpoints =====
    async getBots(): Promise<Bot[]> {
        return this.request<Bot[]>('/bots', {
            headers: this.getAuthHeaders(),
        });
    }

    async getBot(id: string): Promise<Bot> {
        return this.request<Bot>(`/bots/${id}`, {
            headers: this.getAuthHeaders(),
        });
    }

    async getBotStatus(id: string): Promise<BotStatus> {
        return this.request<BotStatus>(`/bots/${id}/status`, {
            headers: this.getAuthHeaders(),
        });
    }

    async createBot(data: BotCreate): Promise<Bot> {
        return this.request<Bot>('/bots', {
            method: 'POST',
            body: JSON.stringify(data),
            headers: this.getAuthHeaders(),
        });
    }

    async updateBot(id: string, data: Partial<BotCreate>): Promise<Bot> {
        return this.request<Bot>(`/bots/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
            headers: this.getAuthHeaders(),
        });
    }

    async deleteBot(id: string): Promise<void> {
        return this.request<void>(`/bots/${id}`, {
            method: 'DELETE',
            headers: this.getAuthHeaders(),
        });
    }

    async startBot(id: string): Promise<{ message: string }> {
        return this.request<{ message: string }>(`/bots/${id}/start`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
        });
    }

    async stopBot(id: string): Promise<{ message: string }> {
        return this.request<{ message: string }>(`/bots/${id}/stop`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
        });
    }

    async restartBot(id: string): Promise<{ message: string }> {
        return this.request<{ message: string }>(`/bots/${id}/restart`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
        });
    }

    async healthCheck(id: string): Promise<any> {
        return this.request<any>(`/bots/${id}/health-check`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
        });
    }

    // ===== Conversation endpoints =====
    async getConversations(botId?: string): Promise<Conversation[]> {
        const params = botId ? `?bot_id=${encodeURIComponent(botId)}` : '';
        return this.request<Conversation[]>(`/conversations${params}`, {
            headers: this.getAuthHeaders(),
        });
    }
}

export const apiClient = new ApiClient();
