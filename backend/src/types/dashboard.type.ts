// 대시보드 관련 타입 정의

export interface ScanHistory {
    id: number;
    user_id: number;
    product_name: string;
    risk_level: 'green' | 'yellow' | 'red';
    risk_score: number;
    risk_reason: string;
    calories?: number;
    carbs?: number;
    protein?: number;
    fat?: number;
    detected_ingredients?: string[];
    detected_allergens?: string[];
    diet_warnings?: string[];
    ocr_full_result?: any;
    scanned_at: Date;
}

export interface DashboardStats {
    scan_count: number;
    risk_distribution: {
        green: number;
        yellow: number;
        red: number;
    };
    allergen_frequency: { [key: string]: number };
    diet_violation_count: number;
    avg_nutrition: {
        calories: number;
        carbs: number;
        protein: number;
        fat: number;
    };
}

export interface DashboardPeriod {
    period: 'week' | 'month' | 'all';
}
