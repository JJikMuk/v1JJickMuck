# 📚 API 명세서

프로젝트의 전체 API 명세서입니다.

## 📖 목차

1. [인증 API](./API_Authentication.md) - 회원가입, 로그인
2. [사용자 프로필 API](./API_UserProfile.md) - 프로필 조회, 수정
3. [이미지 업로드 API](./API_ImageUpload.md) - 이미지 업로드, FastAPI 연동

---

## 🌐 Base URL

```
http://localhost:3000
```

---

## 🔑 인증 방식

대부분의 API는 JWT Bearer Token 인증이 필요합니다.

### 인증 흐름

1. **회원가입**: `POST /api/auth/register`
2. **로그인**: `POST /api/auth/login` → JWT 토큰 발급
3. **토큰 사용**: 이후 요청 시 `Authorization: Bearer <token>` 헤더 포함

### 예시

```javascript
const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';

fetch('http://localhost:3000/api/users/profile', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

---

## 📋 API 엔드포인트 요약

### 인증 (Authentication)

| Method | Endpoint | 인증 필요 | 설명 |
|--------|----------|----------|------|
| POST | `/api/auth/register` | ❌ | 회원가입 |
| POST | `/api/auth/login` | ❌ | 로그인 (JWT 발급) |

### 사용자 프로필 (User Profile)

| Method | Endpoint | 인증 필요 | 설명 |
|--------|----------|----------|------|
| GET | `/api/users/profile` | ✅ | 프로필 조회 |
| PATCH | `/api/users/profile` | ✅ | 프로필 수정 (알레르기, 식단) |

### 이미지 업로드 (Image Upload)

| Method | Endpoint | 인증 필요 | 설명 |
|--------|----------|----------|------|
| POST | `/api/images/upload` | ✅ | 이미지 업로드 → FastAPI 처리 |
| GET | `/api/images/health` | ❌ | FastAPI 서버 상태 확인 |

---

## 🎯 빠른 시작

### 1. 회원가입

```bash
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### 2. 로그인

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

응답에서 `token`을 저장합니다.

### 3. 프로필 조회

```bash
curl -X GET http://localhost:3000/api/users/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. 프로필 수정

```bash
curl -X PATCH http://localhost:3000/api/users/profile \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "diet_type": "vegetarian",
    "allergy_ids": [1, 3, 5]
  }'
```

### 5. 이미지 업로드

```bash
curl -X POST http://localhost:3000/api/images/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "image=@/path/to/image.jpg"
```

---

## 🔧 환경 설정

### .env 파일

```env
# Server
PORT=3000

# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=your_database

# JWT
JWT_SECRET=your_jwt_secret_key_here

# FastAPI
FASTAPI_URL=http://localhost:8000
```

---

## 📊 응답 형식

### 성공 응답

```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... }
}
```

### 오류 응답

```json
{
  "success": false,
  "message": "Error message",
  "error": "Detailed error description"
}
```

---

## 🚨 HTTP Status Code

| Code | 설명 |
|------|------|
| `200` | 성공 |
| `201` | 생성 성공 |
| `400` | 잘못된 요청 |
| `401` | 인증 실패 |
| `500` | 서버 오류 |
| `503` | 서비스 사용 불가 |

---

## 📁 데이터베이스 스키마

### USERS 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT | PK, AUTO_INCREMENT |
| uuid | VARCHAR(36) | UUID, UNIQUE |
| email | VARCHAR(255) | 이메일, UNIQUE |
| password | VARCHAR(255) | bcrypt 해시 |
| diet_type | VARCHAR(50) | 식단 타입 |
| created_at | TIMESTAMP | 생성일 |
| updated_at | TIMESTAMP | 수정일 |

### ALLERGIES 테이블 (마스터 데이터)

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

### USER_ALLERGIES 테이블 (관계 테이블)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT | PK, AUTO_INCREMENT |
| user_id | INT | FK → USERS.id |
| allergy_id | INT | FK → ALLERGIES.id |
| created_at | TIMESTAMP | 생성일 |

---

## 🛠️ 개발 도구

### Postman Collection

API 테스트를 위한 Postman Collection을 제공합니다. (TODO: 추가 예정)

### Swagger/OpenAPI

API 문서를 Swagger UI로 확인할 수 있습니다. (TODO: 추가 예정)

---

## 📞 문의

API 사용 중 문제가 발생하면 이슈를 등록해주세요.
