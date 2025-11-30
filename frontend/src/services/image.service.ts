import { api } from './api';
import type { ImageUploadResponse, ApiResponse } from '../types';

export const imageService = {
  async uploadImage(file: File): Promise<ImageUploadResponse> {
    const formData = new FormData();
    formData.append('image', file);

    const response = await api.fetch('/images/upload', {
      method: 'POST',
      body: formData,
    });

    return response.json();
  },

  async checkFastAPIHealth(): Promise<ApiResponse> {
    const response = await api.fetch('/images/health', {
      method: 'GET',
    });

    return response.json();
  },
};
