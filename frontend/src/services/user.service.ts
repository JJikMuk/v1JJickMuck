import { api } from './api';

export const userService = {
  // 기본 프로필 조회
  getProfile: async () => {
    const response = await api.fetch('/users/profile');  // /user → /users
    if (!response.ok) {
      throw new Error('Failed to get profile');
    }
    return response.json();
  },

  // 전체 프로필 조회 (RAG용)
  getFullProfile: async () => {
    const response = await api.fetch('/users/profile/full');  // /user → /users
    if (!response.ok) {
      throw new Error('Failed to get full profile');
    }
    return response.json();
  },

  // 기본 프로필 업데이트 (식단, 알레르기)
  updateProfile: async (data: {
    diet_type?: string;
    allergy_ids?: number[];
  }) => {
    const response = await api.fetch('/users/profile', {  // /user → /users
      method: 'PUT',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error('Failed to update profile');
    }
    return response.json();
  },

  // 건강 프로필 업데이트 (키, 몸무게, 연령대, 성별)
  updateHealthProfile: async (data: {
    height?: number;
    weight?: number;
    age_range?: string;
    gender?: string;
  }) => {
    const response = await api.fetch('/users/profile/health', {  // /user → /users
      method: 'PUT',
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error('Failed to update health profile');
    }
    return response.json();
  },

  // 전체 질병 목록 조회
  getAllDiseases: async () => {
    const response = await api.fetch('/users/diseases/all');
    if (!response.ok) {
      throw new Error('Failed to get diseases');
    }
    return response.json();
  },

  // 내 질병 업데이트
  updateDiseases: async (diseaseIds: number[]) => {
    const response = await api.fetch('/users/diseases', {
      method: 'PUT',
      body: JSON.stringify({ disease_ids: diseaseIds }),
    });
    if (!response.ok) {
      throw new Error('Failed to update diseases');
    }
    return response.json();
  },

  // 전체 특수 상태 목록 조회
  getAllSpecialConditions: async () => {
    const response = await api.fetch('/users/conditions/all');
    if (!response.ok) {
      throw new Error('Failed to get special conditions');
    }
    return response.json();
  },

  // 내 특수 상태 업데이트
  updateSpecialConditions: async (conditionIds: number[]) => {
    const response = await api.fetch('/users/conditions', {
      method: 'PUT',
      body: JSON.stringify({ condition_ids: conditionIds }),
    });
    if (!response.ok) {
      throw new Error('Failed to update special conditions');
    }
    return response.json();
  },
};
