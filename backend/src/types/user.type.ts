// User 관련 타입 정의

export type DietType = 'vegetarian' | 'vegan' | 'halal' | 'kosher' | 'pescatarian' | 'none';

export interface Allergy {
    name: string;
    display_name: string;
}

export interface User {
    uuid: string;
    email: string;
    password: string;
    name: string;
    diet_type?: DietType | null;
    allergies?: Allergy[];
    created_at?: Date;
    updated_at?: Date;
}

export interface UserRegistrationRequest {
    email: string;
    password: string;
    name: string;
}

export interface UserLoginRequest {
    email: string;
    password: string;
}

export interface UserLoginResponse {
    message: string;
    token: string;
}

export interface UserRegistrationResponse {
    message: string;
    uuid: string;
}

export interface UserProfileUpdateRequest {
    diet_type?: DietType | null;
    allergy_ids?: number[];  // ALLERGIES 테이블의 id 배열
}