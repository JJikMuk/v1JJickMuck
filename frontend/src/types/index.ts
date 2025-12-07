// Auth Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  accessToken?: string;
}

export interface User {
  uuid: string;
  email: string;
  name: string;
  diet_type: string | null;
  allergies: Allergy[];
  // 새로 추가된 필드
  height: number | null;
  weight: number | null;
  age_range: string | null;
  gender: string | null;
  diseases?: Disease[];
  special_conditions?: SpecialCondition[];
}

export interface Allergy {
  allergy_id: number;
  allergy_name: string;
  display_name?: string;
}

// 새로 추가
export interface Disease {
  id: number;
  name: string;
  display_name: string;
}

// 새로 추가
export interface SpecialCondition {
  id: number;
  name: string;
  display_name: string;
}

// 전체 프로필 타입 (RAG API용)
export interface UserFullProfile {
  user_id: string;
  email: string;
  name: string;
  diet_type: string | null;
  height: number | null;
  weight: number | null;
  age_range: string | null;
  gender: string | null;
  allergies: string[];
  diseases: string[];
  special_conditions: string[];
}

// Image Upload Types
export interface ImageUploadResponse {
  success: boolean;
  message: string;
  data?: {
    filename: string;
    fastapi_response?: AnalysisResult;
  };
}

export interface AnalysisResult {
  status: string;
  risk_level: 'red' | 'yellow' | 'green';
  risk_score: number;
  analysis: {
    detected_ingredients: string[];
    allergen_warnings: AllergenWarning[];
    diet_warnings: DietWarning[];
  };
  recommendation: string;
  ocr_text?: string;
}

export interface AllergenWarning {
  allergen: string;
  severity: 'high' | 'medium' | 'low';
  message: string;
}

export interface DietWarning {
  ingredient: string;
  reason: string;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
}
