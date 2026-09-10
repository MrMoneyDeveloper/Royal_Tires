export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.status = status;
  }
}

export function createApi(
  credentials,
  { baseUrl = import.meta.env?.VITE_API_URL, onUnauthorized } = {},
) {
  if (!baseUrl)
    throw new ApiError(
      'The API address is not configured. Set VITE_API_URL and restart the frontend.',
    );
  const url = new URL(baseUrl);
  if (
    !['http:', 'https:'].includes(url.protocol) ||
    url.username ||
    url.password
  ) {
    throw new ApiError('The configured API address is invalid.');
  }
  let authorization;
  try {
    authorization = `Basic ${btoa(`${credentials.username}:${credentials.password}`)}`;
  } catch {
    throw new ApiError(
      'Demo credentials must use Basic Auth compatible characters.',
    );
  }

  async function request(path, options = {}) {
    let response;
    try {
      response = await fetch(`${baseUrl.replace(/\/$/, '')}${path}`, {
        ...options,
        headers: { Authorization: authorization, ...options.headers },
        signal: options.signal ?? AbortSignal.timeout(30000),
      });
    } catch {
      throw new ApiError(
        'Unable to reach the API. Check that the backend is running, then try again.',
      );
    }
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      if (response.status === 401) onUnauthorized?.();
      const message = Array.isArray(body?.detail)
        ? body.detail
            .map((item) => `${item.loc?.at(-1) ?? 'Input'}: ${item.msg}`)
            .join(' ')
        : body?.detail;
      throw new ApiError(
        typeof message === 'string'
          ? message
          : 'The request could not be completed.',
        response.status,
      );
    }
    return body;
  }

  return {
    listRequests: (limit = 50, offset = 0) =>
      request(`/api/requests?limit=${limit}&offset=${offset}`),
    getRequest: (id) => request(`/api/requests/${id}`),
    createRequest: (data) =>
      request('/api/requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }),
    getZendeskSetup: () => request('/api/zendesk/setup'),
    connectZendesk: () =>
      request('/api/zendesk/connect', {
        method: 'POST',
      }),
    applyZendeskSetup: (planFingerprint) =>
      request('/api/zendesk/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          confirm: true,
          plan_fingerprint: planFingerprint,
        }),
      }),
  };
}
