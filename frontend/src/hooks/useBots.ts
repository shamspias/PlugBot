import {useCallback, useEffect, useState} from 'react';
import {Bot} from '@/types';
import {apiClient} from '@/lib/api/client';

export const useBots = () => {
    const [bots, setBots] = useState<Bot[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchBots = useCallback(async () => {
        try {
            setLoading(true);
            const data = await apiClient.getBots();
            setBots(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchBots();
    }, [fetchBots]);

    return {bots, loading, error, refresh: fetchBots};
};
