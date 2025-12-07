# 📘 인증 (Authentication) API 명세서

## 기본 정보
- **Base URL**: `http://localhost:3000/api/auth`
- **Content-Type**: `application/json`

---

## 1. 회원가입

### **POST** `/api/auth/register`

사용자 계정을 생성합니다.

#### Request

```http
POST /api/auth/register
Content-Type: application/json
```

**Body Parameters:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `email` | string | ✅ | 이메일 주소 (유효한 이메일 형식) |
| `password` | string | ✅ | 비밀번호 (최소 12자) |

**Request Example:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### Response

**Success (201 Created):**
```json
{
  "message": "User registered successfully",
  "uuid": "550e8400-e29b-41d4-a716-446655440001"
}
```

**Error Responses:**

**400 Bad Request - 필드 누락:**
```json
{
  "error": "Email and password are required"
}
```

**400 Bad Request - 이메일 형식 오류:**
```json
{
  "error": "Invalid email format"
}
```

**400 Bad Request - 비밀번호 길이 부족:**
```json
{
  "error": "Password must be at least 12 characters"
}
```

**400 Bad Request - 이메일 중복:**
```json
{
  "error": "Email already exists"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error"
}
```

#### 구현 세부사항
- 이메일 중복 체크
- 비밀번호 bcrypt 해싱 (saltRounds: 10)
- UUID 자동 생성
- 트랜잭션 처리

---

## 2. 로그인

### **POST** `/api/auth/login`

사용자 인증 후 JWT 토큰을 발급합니다.

#### Request

```http
POST /api/auth/login
Content-Type: application/json
```

**Body Parameters:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `email` | string | ✅ | 등록된 이메일 주소 |
| `password` | string | ✅ | 계정 비밀번호 |

**Request Example:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### Response

**Success (200 OK):**
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses:**

**400 Bad Request - 필드 누락:**
```json
{
  "error": "Email and password are required"
}
```

**400 Bad Request - 인증 실패:**
```json
{
  "error": "Invalid email or password"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error"
}
```

#### JWT 토큰 정보
- **Algorithm**: HS256
- **Payload**: `{ uuid: string }`
- **Expiration**: 1시간
- **Usage**: 인증이 필요한 API 요청 시 `Authorization: Bearer <token>` 헤더에 포함

#### 구현 세부사항
- 이메일로 사용자 조회
- bcrypt로 비밀번호 검증
- JWT 토큰 생성 및 반환
- 보안: 이메일/비밀번호 오류 시 동일한 메시지 반환

---

## HTTP Status Code

| HTTP Status | 설명 |
|-------------|------|
| `200` | 성공 (로그인) |
| `201` | 생성 성공 (회원가입) |
| `400` | 잘못된 요청 (유효성 검사 실패, 인증 실패) |
| `500` | 서버 오류 |

---

## 사용 예시

### JavaScript/Fetch

```javascript
// 회원가입
const registerResponse = await fetch('http://localhost:3000/api/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'securepassword123'
  })
});

const registerData = await registerResponse.json();
console.log(registerData.uuid);

// 로그인
const loginResponse = await fetch('http://localhost:3000/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'securepassword123'
  })
});

const loginData = await loginResponse.json();
const token = loginData.token;

// 토큰을 로컬스토리지에 저장
localStorage.setItem('token', token);
```

### cURL

```bash
# 회원가입
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'

# 로그인
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```
