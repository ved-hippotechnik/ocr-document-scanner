import { useState, useCallback } from 'react';
import api from '../utils/apiClient';

const PREFIX = '/api/v3/developer';

async function request(path, options = {}) {
  const { data } = await api({ url: `${PREFIX}${path}`, ...options });
  // The unified v3 envelope wraps payload under `data`, but for backward
  // compatibility with existing UI code we return the inner `data` field
  // when present, otherwise the full response.
  return data.data ?? data;
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
      const msg = err.response?.data?.error?.message || err.message;
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // ── API Keys ──────────────────────────────────────────────────────────
  const listKeys = useCallback(() => call(() => request('/keys')), [call]);
  const createKey = useCallback(
    (body) => call(() => request('/keys', { method: 'POST', data: body })),
    [call],
  );
  const updateKey = useCallback(
    (id, body) => call(() => request(`/keys/${id}`, { method: 'PATCH', data: body })),
    [call],
  );
  const revokeKey = useCallback(
    (id) => call(() => request(`/keys/${id}`, { method: 'DELETE' })),
    [call],
  );

  // ── Usage ─────────────────────────────────────────────────────────────
  const getUsage = useCallback(
    (days = 30) => call(() => request(`/usage?days=${days}`)),
    [call],
  );
  const getKeyUsage = useCallback(
    (id, days = 30) => call(() => request(`/usage/keys/${id}?days=${days}`)),
    [call],
  );

  // ── Webhooks ──────────────────────────────────────────────────────────
  const listWebhooks = useCallback(() => call(() => request('/webhooks')), [call]);
  const createWebhook = useCallback(
    (body) => call(() => request('/webhooks', { method: 'POST', data: body })),
    [call],
  );
  const updateWebhook = useCallback(
    (id, body) => call(() => request(`/webhooks/${id}`, { method: 'PATCH', data: body })),
    [call],
  );
  const deleteWebhook = useCallback(
    (id) => call(() => request(`/webhooks/${id}`, { method: 'DELETE' })),
    [call],
  );
  const testWebhook = useCallback(
    (id) => call(() => request(`/webhooks/${id}/test`, { method: 'POST' })),
    [call],
  );
  const listDeliveries = useCallback(
    (id, page = 1) => call(() => request(`/webhooks/${id}/deliveries?page=${page}`)),
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
