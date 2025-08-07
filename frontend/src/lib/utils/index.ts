export const formatDate = (iso?: string) =>
    iso ? new Date(iso).toLocaleString() : '—';
