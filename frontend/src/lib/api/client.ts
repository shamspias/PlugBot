import {Bot, BotCreate, BotStatus, Conversation} from '@/types';

class ApiClient {
    private baseUrl: string;

    constructor() {
        // Use the full HTTPS URL directly, no proxying
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8531/api/v1';

        // Force HTTPS in production
        if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
            this.baseUrl = apiUrl.replace(/^http:/, 'https:');
        } else {
            this.baseUrl = apiUrl;
        }

        // Ensure no trailing slash
        this.baseUrl = this.baseUrl.replace(/\/$/, '');

        console.log('API Client initialized with baseUrl:', this.baseUrl);
    }

    private getAuthHeaders(): HeadersInit {
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
        return {
            'Content-Type': 'application/json',
            ...(token ? {Authorization: `Bearer ${token}`} : {}),
        };
    }

    private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
        // Ensure endpoint starts with /
        const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
        const url = `${this.baseUrl}${normalizedEndpoint}`;

        // Log the request URL in development
        if (process.env.NODE_ENV === 'development') {
            console.log('API Request:', url);
        }

        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...this.getAuthHeaders(),
                ...options?.headers,
            },
            // Ensure credentials are included for CORS
            credentials: 'include',
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
        });
    }

    async register(data: any): Promise<any> {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async logout(): Promise<void> {
        return this.request('/auth/logout', {
            method: 'POST',
        });
    }

    async getCurrentUser(): Promise<any> {
        return this.request('/auth/me');
    }

    async refreshAccessToken(refreshToken: string): Promise<any> {
        return this.request('/auth/refresh', {
            method: 'POST',
            body: JSON.stringify({refresh_token: refreshToken}),
        });
    }

    async requestPasswordReset(email: string): Promise<any> {
        return this.request('/auth/forgot-password', {
            method: 'POST',
            body: JSON.stringify({email}),
        });
    }

    async resetPassword(token: string, newPassword: string): Promise<any> {
        return this.request('/auth/reset-password', {
            method: 'POST',
            body: JSON.stringify({
                token,
                new_password: newPassword
            })
        });
    }

    // ===== Bot endpoints =====
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

    // ===== Conversation endpoints =====
    async getConversations(botId?: string): Promise<Conversation[]> {
        const params = botId ? `?bot_id=${encodeURIComponent(botId)}` : '';
        return this.request<Conversation[]>(`/conversations${params}`);
    }
}

export const apiClient = new ApiClient();