const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api';

export const api = {
  // Helper to get token
  getToken: () => localStorage.getItem('token'),

  // Helper to set token
  setToken: (token: string) => localStorage.setItem('token', token),

  // Helper to remove token
  removeToken: () => localStorage.removeItem('token'),

  // Base fetch with auth
  async fetch(endpoint: string, options: RequestInit = {}) {
    const token = this.getToken();

    const headers: HeadersInit = {
      ...options.headers,
    };

    // Add authorization header if token exists
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Add Content-Type for JSON if not FormData
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    return response;
  },
};

// Dashboard API functions
export const dashboardApi = {
  /**
   * Get dashboard statistics
   * @param period - 'week' | 'month' | 'all'
   */
  async getStats(period: 'week' | 'month' | 'all' = 'week') {
    const response = await api.fetch(`/dashboard/stats?period=${period}`);
    if (!response.ok) {
      throw new Error('Failed to fetch dashboard stats');
    }
    const data = await response.json();
    return data.data;
  },

  /**
   * Get scan history
   * @param period - 'week' | 'month' | 'all'
   */
  async getHistory(period: 'week' | 'month' | 'all' = 'week') {
    const response = await api.fetch(`/dashboard/history?period=${period}`);
    if (!response.ok) {
      throw new Error('Failed to fetch scan history');
    }
    const data = await response.json();
    return data.data;
  },
};
