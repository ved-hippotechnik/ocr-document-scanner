import { useState, useCallback } from 'react';
import config from '../config';

const BASE = config.endpoints.developerKeys?.replace('/keys', '') ||
  `${config.API_URL}/api/developer`;

function authHeaders() {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function api(path, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000);
  try {
    const res = await fetch(`${BASE}${path}`, {
      headers: authHeaders(),
      signal: controller.signal,
      ...options,
    });
    clearTimeout(timeoutId);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return data;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timed out');
    }
    throw error;
  }
}

export function useDeveloperApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const call = useCallback(async (fn) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // ── API Keys ──────────────────────────────────────────────────────────
  const listKeys = useCallback(() => call(() => api('/keys')), [call]);
  const createKey = useCallback(
    (body) => call(() => api('/keys', { method: 'POST', body: JSON.stringify(body) })),
    [call],
  );
  const updateKey = useCallback(
    (id, body) => call(() => api(`/keys/${id}`, { method: 'PATCH', body: JSON.stringify(body) })),
    [call],
  );
  const revokeKey = useCallback(
    (id) => call(() => api(`/keys/${id}`, { method: 'DELETE' })),
    [call],
  );

  // ── Usage ─────────────────────────────────────────────────────────────
  const getUsage = useCallback(
    (days = 30) => call(() => api(`/usage?days=${days}`)),
    [call],
  );
  const getKeyUsage = useCallback(
    (id, days = 30) => call(() => api(`/usage/keys/${id}?days=${days}`)),
    [call],
  );

  // ── Webhooks ──────────────────────────────────────────────────────────
  const listWebhooks = useCallback(() => call(() => api('/webhooks')), [call]);
  const createWebhook = useCallback(
    (body) => call(() => api('/webhooks', { method: 'POST', body: JSON.stringify(body) })),
    [call],
  );
  const updateWebhook = useCallback(
    (id, body) => call(() => api(`/webhooks/${id}`, { method: 'PATCH', body: JSON.stringify(body) })),
    [call],
  );
  const deleteWebhook = useCallback(
    (id) => call(() => api(`/webhooks/${id}`, { method: 'DELETE' })),
    [call],
  );
  const testWebhook = useCallback(
    (id) => call(() => api(`/webhooks/${id}/test`, { method: 'POST' })),
    [call],
  );
  const listDeliveries = useCallback(
    (id, page = 1) => call(() => api(`/webhooks/${id}/deliveries?page=${page}`)),
    [call],
  );

  return {
    loading,
    error,
    listKeys, createKey, updateKey, revokeKey,
    getUsage, getKeyUsage,
    listWebhooks, createWebhook, updateWebhook, deleteWebhook,
    testWebhook, listDeliveries,
  };
}

export default useDeveloperApi;
