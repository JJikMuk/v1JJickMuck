import { api } from './api';
import type { User, ApiResponse } from '../types';

export const userService = {
  async getProfile(): Promise<ApiResponse<User>> {
    const response = await api.fetch('/users/profile', {
      method: 'GET',
    });

    return response.json();
  },

  async updateProfile(data: {
    name?: string;
    diet_type?: string;
    allergy_ids?: number[];
  }): Promise<ApiResponse<User>> {
    const response = await api.fetch('/users/profile', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });

    return response.json();
  },
};
