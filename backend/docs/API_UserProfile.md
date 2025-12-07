# 📘 사용자 프로필 (User Profile) API 명세서

## 기본 정보
- **Base URL**: `http://localhost:3000/api/users`
- **Content-Type**: `application/json`
- **인증 필수**: ✅ 모든 엔드포인트에 JWT 토큰 필요

---

## 1. 프로필 조회

### **GET** `/api/users/profile`

현재 로그인한 사용자의 프로필 정보를 조회합니다.

#### Request

```http
GET /api/users/profile
Authorization: Bearer <JWT_TOKEN>
```

**Headers:**

| 헤더 | 값 | 필수 |
|------|------|------|
| `Authorization` | `Bearer <token>` | ✅ |

#### Response

**Success (200 OK):**
```json
{
  "success": true,
  "data": {
    "uuid": "550e8400-e29b-41d4-a716-446655440001",
    "email": "user@example.com",
    "diet_type": "vegetarian",
    "allergies": [
      {
        "name": "peanut",
        "display_name": "땅콩"
      },
      {
        "name": "dairy",
        "display_name": "유제품"
      }
    ],
    "created_at": "2024-01-01T00:00:00.000Z",
    "updated_at": "2024-01-15T10:30:00.000Z"
  }
}
```

**Response Fields:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `uuid` | string | 사용자 고유 ID |
| `email` | string | 이메일 주소 |
| `diet_type` | string \| null | 식단 타입 (vegetarian, vegan, halal, kosher, pescatarian, none) |
| `allergies` | array | 알레르기 목록 |
| `allergies[].name` | string | 알레르기 영문명 |
| `allergies[].display_name` | string | 알레르기 한글명 |
| `created_at` | string | 계정 생성일 (ISO 8601) |
| `updated_at` | string | 마지막 수정일 (ISO 8601) |

**Error Responses:**

**401 Unauthorized - 토큰 누락:**
```json
{
  "error": "Token is missing. Please log in."
}
```

**401 Unauthorized - 토큰 만료/유효하지 않음:**
```json
{
  "success": false,
  "message": "Invalid Access Token."
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "message": "Failed to retrieve user profile."
}
```

#### 구현 세부사항
- JWT 토큰에서 UUID 추출
- UUID로 사용자 정보 조회
- 3-way JOIN으로 알레르기 정보 조회 (USERS → USER_ALLERGIES → ALLERGIES)
- 비밀번호는 응답에 포함되지 않음

---

## 2. 프로필 수정

### **PATCH** `/api/users/profile`

현재 로그인한 사용자의 식단 타입 및 알레르기 정보를 수정합니다.

#### Request

```http
PATCH /api/users/profile
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**Headers:**

| 헤더 | 값 | 필수 |
|------|------|------|
| `Authorization` | `Bearer <token>` | ✅ |
| `Content-Type` | `application/json` | ✅ |

**Body Parameters:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `diet_type` | string \| null | ❌ | 식단 타입 |
| `allergy_ids` | number[] | ❌ | 알레르기 ID 배열 |

**유효한 diet_type 값:**
- `vegetarian` - 채식주의
- `vegan` - 비건
- `halal` - 할랄
- `kosher` - 코셔
- `pescatarian` - 페스코 채식 (생선 섭취)
- `none` - 없음
- `null` - 설정 안 함

**Request Examples:**

**식단 타입만 수정:**
```json
{
  "diet_type": "vegan"
}
```

**알레르기만 수정:**
```json
{
  "allergy_ids": [1, 3, 5]
}
```

**둘 다 수정:**
```json
{
  "diet_type": "vegetarian",
  "allergy_ids": [1, 3]
}
```

**알레르기 모두 제거:**
```json
{
  "allergy_ids": []
}
```

**알레르기 ID 참고:**

| ID | name | display_name |
|----|------|--------------|
| 1 | peanut | 땅콩 |
| 2 | tree_nuts | 견과류 |
| 3 | dairy | 유제품 |
| 4 | egg | 계란 |
| 5 | shellfish | 갑각류 |
| 6 | fish | 생선 |
| 7 | soy | 콩 |
| 8 | wheat | 밀 |
| 9 | sesame | 참깨 |
| 10 | gluten | 글루텐 |

#### Response

**Success (200 OK):**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "uuid": "550e8400-e29b-41d4-a716-446655440001",
    "email": "user@example.com",
    "diet_type": "vegetarian",
    "allergies": [
      {
        "name": "peanut",
        "display_name": "땅콩"
      },
      {
        "name": "dairy",
        "display_name": "유제품"
      }
    ],
    "created_at": "2024-01-01T00:00:00.000Z",
    "updated_at": "2024-01-15T10:35:00.000Z"
  }
}
```

**Error Responses:**

**400 Bad Request - 유효하지 않은 diet_type:**
```json
{
  "success": false,
  "message": "Invalid diet_type. Must be one of: vegetarian, vegan, halal, kosher, pescatarian, none"
}
```

**400 Bad Request - allergy_ids가 배열이 아님:**
```json
{
  "success": false,
  "message": "allergy_ids must be an array"
}
```

**401 Unauthorized - 토큰 누락/만료:**
```json
{
  "error": "Token is missing. Please log in."
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "message": "Failed to update user profile."
}
```

#### 구현 세부사항
- JWT 토큰에서 UUID 추출
- 트랜잭션으로 처리:
  1. USERS 테이블의 diet_type 업데이트
  2. USER_ALLERGIES 테이블의 기존 데이터 삭제
  3. 새로운 알레르기 데이터 삽입
- 업데이트된 전체 프로필 정보 반환

---

## HTTP Status Code

| HTTP Status | 설명 |
|-------------|------|
| `200` | 성공 |
| `400` | 잘못된 요청 (유효성 검사 실패) |
| `401` | 인증 실패 (토큰 누락/만료) |
| `500` | 서버 오류 |

---

## 사용 예시

### JavaScript/Fetch

```javascript
// 로그인 후 토큰 저장
const token = localStorage.getItem('token');

// 프로필 조회
const getProfile = async () => {
  const response = await fetch('http://localhost:3000/api/users/profile', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  const data = await response.json();
  console.log(data);
};

// 프로필 수정
const updateProfile = async () => {
  const response = await fetch('http://localhost:3000/api/users/profile', {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      diet_type: 'vegan',
      allergy_ids: [1, 3, 5]  // 땅콩, 유제품, 갑각류
    })
  });

  const data = await response.json();
  console.log(data);
};
```

### cURL

```bash
# 프로필 조회
curl -X GET http://localhost:3000/api/users/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 프로필 수정
curl -X PATCH http://localhost:3000/api/users/profile \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "diet_type": "vegetarian",
    "allergy_ids": [1, 3]
  }'
```

---

## 데이터 흐름

```
1. 클라이언트: JWT 토큰과 함께 요청
   ↓
2. auth.middleware: 토큰 검증 → req.user.uuid 추출
   ↓
3. UserController: 요청 처리
   ↓
4. UserService: 비즈니스 로직
   ↓
5. UserModel: DB 조회/수정
   - USERS 테이블
   - USER_ALLERGIES 테이블 (JOIN)
   - ALLERGIES 테이블 (JOIN)
   ↓
6. 클라이언트: JSON 응답 수신
```
