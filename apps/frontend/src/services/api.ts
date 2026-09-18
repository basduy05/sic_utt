const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (typeof window !== 'undefined') {
    const geminiKey = localStorage.getItem('gemini_api_key');
    if (geminiKey) {
      defaultHeaders['x-gemini-api-key'] = geminiKey;
    }
  }

  if (options.body instanceof FormData) {
    delete defaultHeaders['Content-Type'];
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);

  try {
    const response = await fetch(url, {
      ...options,
      signal: options.signal || controller.signal,
      headers: {
        ...defaultHeaders,
        ...(options.headers as Record<string, string>),
      },
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'API Error' }));
      throw new Error(errorData.detail || `HTTP Error ${response.status}`);
    }

    return response.json();
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error('Kết nối tới máy chủ AI quá thời gian (Timeout 15s). Vui lòng thử lại.');
    }
    throw err;
  }
}
