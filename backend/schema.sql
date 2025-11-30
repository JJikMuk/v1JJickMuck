-- ====================================
-- 유저 테이블
-- ====================================
CREATE TABLE USERS (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    diet_type VARCHAR(50) DEFAULT NULL COMMENT 'vegetarian, vegan, halal, kosher, pescatarian, none',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_uuid (uuid),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================
-- 알레르기 마스터 테이블
-- ====================================
CREATE TABLE ALLERGIES (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL COMMENT '알레르기 영문명 (예: peanut, dairy)',
    display_name VARCHAR(100) NOT NULL COMMENT '알레르기 표시명 (예: 땅콩, 유제품)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================
-- 유저-알레르기 관계 테이블 (Many-to-Many)
-- ====================================
CREATE TABLE USER_ALLERGIES (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    allergy_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES USERS(id) ON DELETE CASCADE,
    FOREIGN KEY (allergy_id) REFERENCES ALLERGIES(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_allergy (user_id, allergy_id),
    INDEX idx_user_id (user_id),
    INDEX idx_allergy_id (allergy_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================
-- 기본 알레르기 데이터 삽입
-- ====================================
INSERT INTO ALLERGIES (name, display_name) VALUES
('peanut', '땅콩'),
('tree_nuts', '견과류'),
('dairy', '유제품'),
('egg', '계란'),
('shellfish', '갑각류'),
('fish', '생선'),
('soy', '콩'),
('wheat', '밀'),
('sesame', '참깨'),
('gluten', '글루텐');

-- ====================================
-- 스캔 히스토리 테이블
-- ====================================
CREATE TABLE SCAN_HISTORY (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_name VARCHAR(255) COMMENT '제품명',
    risk_level ENUM('green', 'yellow', 'red') NOT NULL COMMENT '위험도 레벨',
    risk_score INT COMMENT '위험도 점수 (0-100)',
    risk_reason TEXT COMMENT '위험도 판단 이유',

    -- 영양 정보
    calories DECIMAL(10,2) COMMENT '칼로리 (kcal)',
    carbs DECIMAL(10,2) COMMENT '탄수화물 (g)',
    protein DECIMAL(10,2) COMMENT '단백질 (g)',
    fat DECIMAL(10,2) COMMENT '지방 (g)',

    -- 검출된 정보 (JSON)
    detected_ingredients JSON COMMENT '검출된 원재료 목록',
    detected_allergens JSON COMMENT '검출된 알레르기 성분',
    diet_warnings JSON COMMENT '식단 타입 위반 사항',

    -- OCR 원본 데이터
    ocr_full_result JSON COMMENT 'FastAPI 전체 응답 데이터',

    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '스캔 일시',

    FOREIGN KEY (user_id) REFERENCES USERS(id) ON DELETE CASCADE,
    INDEX idx_user_scanned (user_id, scanned_at),
    INDEX idx_risk_level (risk_level),
    INDEX idx_scanned_at (scanned_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
