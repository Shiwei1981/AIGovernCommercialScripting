import { getAccessToken } from '../auth/authClient.js';

async function request(path, options = {}) {
  const token = await getAccessToken();
  const response = await fetch(`${window.__env?.API_BASE_URL || '/api'}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Request failed (${response.status}): ${detail}`);
  }
  return response.json();
}

export function createGeneration(payload) {
  return request('/generations', { method: 'POST', body: JSON.stringify(payload) });
}

export function searchGenerations(params) {
  const query = new URLSearchParams(params).toString();
  return request(`/generations?${query}`);
}

export function getAuditTrace(generationId) {
  return request(`/generations/${generationId}/audit`);
}
