import { api } from './api';

export interface Allergy {
  id: number;
  name: string;
  display_name: string;
}

export interface AllergyResponse {
  success: boolean;
  data?: Allergy[];
  message?: string;
}

export const allergyService = {
  async getAllAllergies(): Promise<AllergyResponse> {
    const response = await api.fetch('/allergies', {
      method: 'GET',
    });

    return response.json();
  },
};
