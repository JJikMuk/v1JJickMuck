import { api } from './api';
import type { LoginRequest, SignupRequest, AuthResponse } from '../types';

export const authService = {
  async signup(data: SignupRequest): Promise<AuthResponse> {
    const response = await api.fetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    const result = await response.json();

    // Convert backend response format to frontend format
    if (result.message && result.uuid) {
      return {
        success: true,
        message: result.message,
      };
    }

    if (result.error) {
      return {
        success: false,
        message: result.error,
      };
    }

    return result;
  },

  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await api.fetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    const result = await response.json();

    // Convert backend response format to frontend format
    if (result.message && result.token) {
      api.setToken(result.token);
      return {
        success: true,
        message: result.message,
        accessToken: result.token,
      };
    }

    if (result.error) {
      return {
        success: false,
        message: result.error,
      };
    }

    return result;
  },

  async logout() {
    const response = await api.fetch('/auth/logout', {
      method: 'POST',
    });

    // Remove token
    api.removeToken();

    return response.json();
  },

  async refreshToken(): Promise<AuthResponse> {
    const response = await api.fetch('/auth/refresh', {
      method: 'POST',
    });

    const result = await response.json();

    // Update token if refresh successful
    if (result.success && result.accessToken) {
      api.setToken(result.accessToken);
    }

    return result;
  },
};
