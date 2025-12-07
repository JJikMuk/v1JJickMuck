-- ====================================
-- 대시보드 테스트용 더미 데이터
-- user_id = 1 기준
-- ====================================

-- 최근 30일 스캔 히스토리 (다양한 위험도, 알레르기, 영양 정보)

-- 1. 안전한 제품들 (GREEN)
INSERT INTO SCAN_HISTORY (
    user_id, product_name, risk_level, risk_score, risk_reason,
    calories, carbs, protein, fat,
    detected_ingredients, detected_allergens, diet_warnings, ocr_full_result,
    scanned_at
) VALUES
(1, '사과', 'green', 10, '알레르기 성분 없음. 안전하게 섭취 가능합니다.',
 52.0, 14.0, 0.3, 0.2,
 '["사과"]', '[]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 1 DAY)),

(1, '현미밥', 'green', 10, '알레르기 성분 없음. 건강한 선택입니다.',
 150.0, 32.0, 3.0, 1.0,
 '["현미", "물"]', '[]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 2 DAY)),

(1, '닭가슴살 샐러드', 'green', 15, '알레르기 성분 없음. 영양 균형이 좋습니다.',
 180.0, 8.0, 28.0, 5.0,
 '["닭가슴살", "양상추", "토마토", "오이", "올리브오일"]', '[]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 3 DAY)),

(1, '바나나', 'green', 10, '알레르기 성분 없음. 칼륨이 풍부합니다.',
 89.0, 23.0, 1.1, 0.3,
 '["바나나"]', '[]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 4 DAY)),

(1, '두부', 'green', 10, '알레르기 성분 없음. 식물성 단백질 급원입니다.',
 76.0, 1.9, 8.1, 4.8,
 '["대두", "물", "간수"]', '[]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 5 DAY));

-- 2. 주의 제품들 (YELLOW)
INSERT INTO SCAN_HISTORY (
    user_id, product_name, risk_level, risk_score, risk_reason,
    calories, carbs, protein, fat,
    detected_ingredients, detected_allergens, diet_warnings, ocr_full_result,
    scanned_at
) VALUES
(1, '초코칩 쿠키', 'yellow', 50, '유제품 포함 - 비건 부적합. 교차오염 가능성 있음.',
 250.0, 35.0, 3.0, 12.0,
 '["밀가루", "설탕", "버터", "초콜릿칩", "계란"]', '["유제품", "계란"]', '["유제품 포함 - 비건 부적합"]', '{}',
 DATE_SUB(NOW(), INTERVAL 6 DAY)),

(1, '참치 김밥', 'yellow', 45, '참치(생선) 포함. 생선 알레르기 주의.',
 320.0, 45.0, 12.0, 8.0,
 '["밥", "참치", "김", "단무지", "우엉", "계란"]', '["생선", "계란"]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 7 DAY)),

(1, '아몬드 우유', 'yellow', 40, '견과류 포함. 견과류 알레르기 주의.',
 30.0, 1.5, 1.0, 2.5,
 '["아몬드", "물", "설탕"]', '["견과류"]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 8 DAY)),

(1, '새우칩', 'yellow', 55, '갑각류 포함. 알레르기 주의 필요.',
 150.0, 20.0, 2.0, 7.0,
 '["밀가루", "새우", "식용유", "소금"]', '["갑각류", "밀"]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 10 DAY));

-- 3. 위험 제품들 (RED)
INSERT INTO SCAN_HISTORY (
    user_id, product_name, risk_level, risk_score, risk_reason,
    calories, carbs, protein, fat,
    detected_ingredients, detected_allergens, diet_warnings, ocr_full_result,
    scanned_at
) VALUES
(1, '땅콩버터', 'red', 95, '땅콩 직접 포함. 땅콩 알레르기 사용자는 절대 섭취 금지!',
 588.0, 20.0, 25.0, 50.0,
 '["땅콩", "설탕", "소금", "식용유"]', '["땅콩"]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 9 DAY)),

(1, '우유', 'red', 90, '유제품 직접 포함. 유제품 알레르기 사용자는 섭취 금지.',
 61.0, 4.8, 3.2, 3.3,
 '["원유"]', '["유제품"]', '["유제품 포함 - 비건 부적합"]', '{}',
 DATE_SUB(NOW(), INTERVAL 11 DAY)),

(1, '계란 샌드위치', 'red', 85, '계란 직접 포함. 계란 알레르기 사용자는 섭취 금지.',
 280.0, 28.0, 12.0, 14.0,
 '["식빵", "계란", "마요네즈", "소금", "후추"]', '["계란", "밀", "유제품"]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 12 DAY)),

(1, '새우볶음밥', 'red', 90, '갑각류 직접 포함. 새우 알레르기 사용자는 섭취 금지.',
 420.0, 55.0, 18.0, 15.0,
 '["밥", "새우", "계란", "당근", "완두콩", "간장", "참기름"]', '["갑각류", "계란", "콩"]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 13 DAY)),

(1, '호두파이', 'red', 88, '견과류 직접 포함. 견과류 알레르기 사용자는 섭취 금지.',
 450.0, 50.0, 8.0, 25.0,
 '["밀가루", "호두", "버터", "설탕", "계란"]', '["견과류", "밀", "유제품", "계란"]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 14 DAY));

-- 4. 추가 안전한 제품들 (통계 다양화)
INSERT INTO SCAN_HISTORY (
    user_id, product_name, risk_level, risk_score, risk_reason,
    calories, carbs, protein, fat,
    detected_ingredients, detected_allergens, diet_warnings, ocr_full_result,
    scanned_at
) VALUES
(1, '야채 샐러드', 'green', 10, '알레르기 성분 없음. 신선한 채소로 구성.',
 80.0, 12.0, 3.0, 2.0,
 '["양상추", "토마토", "오이", "당근", "올리브오일"]', '[]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 15 DAY)),

(1, '현미 주먹밥', 'green', 10, '알레르기 성분 없음. 간편한 한 끼.',
 200.0, 42.0, 4.0, 2.0,
 '["현미", "소금", "참기름"]', '[]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 16 DAY)),

(1, '오렌지', 'green', 10, '알레르기 성분 없음. 비타민C가 풍부합니다.',
 47.0, 12.0, 0.9, 0.1,
 '["오렌지"]', '[]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 17 DAY)),

(1, '고구마', 'green', 10, '알레르기 성분 없음. 식이섬유가 풍부합니다.',
 86.0, 20.0, 1.6, 0.1,
 '["고구마"]', '[]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 18 DAY)),

(1, '브로콜리', 'green', 10, '알레르기 성분 없음. 영양이 풍부한 채소입니다.',
 34.0, 7.0, 2.8, 0.4,
 '["브로콜리"]', '[]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 20 DAY));

-- 5. 최근 1주일 데이터 추가
INSERT INTO SCAN_HISTORY (
    user_id, product_name, risk_level, risk_score, risk_reason,
    calories, carbs, protein, fat,
    detected_ingredients, detected_allergens, diet_warnings, ocr_full_result,
    scanned_at
) VALUES
(1, '토마토', 'green', 10, '알레르기 성분 없음. 리코펜이 풍부합니다.',
 18.0, 3.9, 0.9, 0.2,
 '["토마토"]', '[]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 1 HOUR)),

(1, '치즈케이크', 'yellow', 50, '유제품 포함. 유제품 알레르기 주의.',
 321.0, 25.0, 6.0, 23.0,
 '["크림치즈", "설탕", "계란", "밀가루", "버터"]', '["유제품", "계란", "밀"]', '["유제품 포함 - 비건 부적합"]', '{}',
 DATE_SUB(NOW(), INTERVAL 3 HOUR)),

(1, '김치', 'green', 10, '알레르기 성분 없음. 유산균이 풍부합니다.',
 15.0, 2.4, 1.1, 0.5,
 '["배추", "고춧가루", "마늘", "생강", "소금"]', '[]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 5 HOUR)),

(1, '연어 스테이크', 'yellow', 45, '생선 포함. 생선 알레르기 주의.',
 206.0, 0.0, 22.0, 13.0,
 '["연어", "소금", "후추", "레몬"]', '["생선"]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 8 HOUR)),

(1, '콩나물', 'green', 10, '알레르기 성분 없음. 저칼로리 고단백 식품입니다.',
 30.0, 5.9, 3.0, 0.2,
 '["콩나물"]', '[]', '[]', '{}',
 DATE_SUB(NOW(), INTERVAL 12 HOUR));

-- 데이터 확인 쿼리
SELECT
    risk_level,
    COUNT(*) as count,
    CONCAT(ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM SCAN_HISTORY WHERE user_id = 1), 1), '%') as percentage
FROM SCAN_HISTORY
WHERE user_id = 1
GROUP BY risk_level;

SELECT COUNT(*) as total_scans FROM SCAN_HISTORY WHERE user_id = 1;
