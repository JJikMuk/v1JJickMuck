-- ====================================
-- 더미 유저 데이터
-- ====================================
-- 비밀번호는 모두 "password1234" (bcrypt 해시값)
INSERT INTO USERS (uuid, email, password, diet_type) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'john.doe@example.com', '$2b$10$rHZv6vGN0qGvO9xKqYZqJuF5YqGqF6Zn8vZ0vZ0vZ0vZ0vZ0vZ0vZ', 'vegetarian'),
('550e8400-e29b-41d4-a716-446655440002', 'jane.smith@example.com', '$2b$10$rHZv6vGN0qGvO9xKqYZqJuF5YqGqF6Zn8vZ0vZ0vZ0vZ0vZ0vZ0vZ', 'vegan'),
('550e8400-e29b-41d4-a716-446655440003', 'mike.wilson@example.com', '$2b$10$rHZv6vGN0qGvO9xKqYZqJuF5YqGqF6Zn8vZ0vZ0vZ0vZ0vZ0vZ0vZ', 'halal'),
('550e8400-e29b-41d4-a716-446655440004', 'sarah.kim@example.com', '$2b$10$rHZv6vGN0qGvO9xKqYZqJuF5YqGqF6Zn8vZ0vZ0vZ0vZ0vZ0vZ0vZ', 'pescatarian'),
('550e8400-e29b-41d4-a716-446655440005', 'david.lee@example.com', '$2b$10$rHZv6vGN0qGvO9xKqYZqJuF5YqGqF6Zn8vZ0vZ0vZ0vZ0vZ0vZ0vZ', NULL);

-- ====================================
-- 더미 유저-알레르기 관계 데이터
-- ====================================
-- john.doe@example.com (id=1) - 땅콩, 유제품 알레르기
INSERT INTO USER_ALLERGIES (user_id, allergy_id) VALUES
(1, 1),  -- peanut
(1, 3);  -- dairy

-- jane.smith@example.com (id=2) - 견과류, 계란, 유제품 알레르기
INSERT INTO USER_ALLERGIES (user_id, allergy_id) VALUES
(2, 2),  -- tree_nuts
(2, 3),  -- dairy
(2, 4);  -- egg

-- mike.wilson@example.com (id=3) - 갑각류, 생선 알레르기
INSERT INTO USER_ALLERGIES (user_id, allergy_id) VALUES
(3, 5),  -- shellfish
(3, 6);  -- fish

-- sarah.kim@example.com (id=4) - 밀, 글루텐 알레르기
INSERT INTO USER_ALLERGIES (user_id, allergy_id) VALUES
(4, 8),  -- wheat
(4, 10); -- gluten

-- david.lee@example.com (id=5) - 알레르기 없음
-- (데이터 없음)

-- ====================================
-- 더미 데이터 조회 예제 쿼리
-- ====================================
-- 유저별 알레르기 정보 조회
SELECT
    u.email,
    u.diet_type,
    GROUP_CONCAT(a.display_name SEPARATOR ', ') as allergies
FROM USERS u
LEFT JOIN USER_ALLERGIES ua ON u.id = ua.user_id
LEFT JOIN ALLERGIES a ON ua.allergy_id = a.id
GROUP BY u.id, u.email, u.diet_type;

-- 특정 유저의 상세 알레르기 정보
SELECT
    u.uuid,
    u.email,
    u.diet_type,
    a.name as allergy_name,
    a.display_name as allergy_display_name
FROM USERS u
LEFT JOIN USER_ALLERGIES ua ON u.id = ua.user_id
LEFT JOIN ALLERGIES a ON ua.allergy_id = a.id
WHERE u.uuid = '550e8400-e29b-41d4-a716-446655440001';
