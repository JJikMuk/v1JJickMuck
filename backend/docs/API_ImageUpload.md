# 📘 이미지 업로드 (Image Upload) API 명세서

## 기본 정보
- **Base URL**: `http://localhost:3000/api/images`
- **Content-Type**: `multipart/form-data` (이미지 업로드)
- **인증**: 이미지 업로드는 JWT 토큰 필요 ✅

---

## 1. 이미지 업로드

### **POST** `/api/images/upload`

이미지를 업로드하고 FastAPI 서버로 전달하여 처리 결과를 반환받습니다.

#### Request

```http
POST /api/images/upload
Authorization: Bearer <JWT_TOKEN>
Content-Type: multipart/form-data
```

**Headers:**

| 헤더 | 값 | 필수 |
|------|------|------|
| `Authorization` | `Bearer <token>` | ✅ |
| `Content-Type` | `multipart/form-data` | ✅ (자동 설정) |

**Form Data:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `image` | File | ✅ | 이미지 파일 (단일 파일) |

**파일 제한:**
- **허용 타입**: 이미지 파일만 (`image/*`)
- **최대 크기**: 10MB
- **지원 형식**: JPEG, PNG, GIF, WebP 등 모든 이미지 포맷

#### Response

**Success (200 OK):**
```json
{
  "success": true,
  "message": "Image uploaded successfully",
  "data": {
    "filename": "photo.jpg",
    "fastapi_response": {
      "result": "분석 결과",
      "confidence": 0.95,
      "labels": ["음식1", "음식2"]
    }
  }
}
```

**Response Fields:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `success` | boolean | 성공 여부 |
| `message` | string | 응답 메시지 |
| `data.filename` | string | 업로드된 파일명 |
| `data.fastapi_response` | object | FastAPI 서버의 처리 결과 |

**Error Responses:**

**400 Bad Request - 파일 누락:**
```json
{
  "success": false,
  "message": "No image file uploaded"
}
```

**400 Bad Request - 이미지 파일이 아님:**
```json
{
  "success": false,
  "message": "Only image files are allowed"
}
```

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

**500 Internal Server Error - FastAPI 오류:**
```json
{
  "success": false,
  "message": "Failed to upload image"
}
```

#### 구현 세부사항
1. multer로 이미지를 메모리 버퍼로 수신
2. 파일 타입 검증 (이미지만 허용)
3. FormData로 FastAPI 서버에 전송
4. FastAPI 처리 결과를 클라이언트에 반환

#### 데이터 흐름
```
Frontend → Node.js (multer) → FastAPI → Node.js → Frontend
   |           |                   |          |
 파일 업로드   버퍼 변환        AI 처리    결과 반환
```

---

## 2. FastAPI 서버 헬스 체크

### **GET** `/api/images/health`

FastAPI 서버의 상태를 확인합니다.

#### Request

```http
GET /api/images/health
```

**Headers:** 없음 (인증 불필요)

#### Response

**Success (200 OK) - FastAPI 서버 정상:**
```json
{
  "success": true,
  "message": "FastAPI server is healthy"
}
```

**Service Unavailable (503) - FastAPI 서버 다운:**
```json
{
  "success": false,
  "message": "FastAPI server is unavailable"
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "message": "Failed to check FastAPI health"
}
```

#### 구현 세부사항
- FastAPI 서버의 `/health` 엔드포인트를 호출
- 응답 성공 여부만 확인

---

## HTTP Status Code

| HTTP Status | 설명 |
|-------------|------|
| `200` | 성공 |
| `400` | 잘못된 요청 (파일 누락, 타입 오류) |
| `401` | 인증 실패 (토큰 누락/만료) |
| `500` | 서버 오류 |
| `503` | FastAPI 서버 사용 불가 |

---

## 사용 예시

### JavaScript/Fetch (FormData)

```javascript
const token = localStorage.getItem('token');

// HTML input element
const fileInput = document.getElementById('imageInput');

const uploadImage = async () => {
  const file = fileInput.files[0];

  if (!file) {
    alert('파일을 선택해주세요');
    return;
  }

  // FormData 생성
  const formData = new FormData();
  formData.append('image', file);

  try {
    const response = await fetch('http://localhost:3000/api/images/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
        // Content-Type은 자동 설정됨 (multipart/form-data)
      },
      body: formData
    });

    const data = await response.json();
    console.log('Upload result:', data);
    console.log('FastAPI response:', data.data.fastapi_response);
  } catch (error) {
    console.error('Upload failed:', error);
  }
};
```

### React Example

```jsx
import { useState } from 'react';

function ImageUpload() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) return;

    setLoading(true);

    const formData = new FormData();
    formData.append('image', file);

    const token = localStorage.getItem('token');

    try {
      const response = await fetch('http://localhost:3000/api/images/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="file"
        accept="image/*"
        onChange={handleFileChange}
      />
      <button type="submit" disabled={!file || loading}>
        {loading ? '업로드 중...' : '업로드'}
      </button>

      {result && (
        <div>
          <h3>결과:</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </form>
  );
}
```

### Axios Example

```javascript
import axios from 'axios';

const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append('image', file);

  const token = localStorage.getItem('token');

  try {
    const response = await axios.post(
      'http://localhost:3000/api/images/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          console.log(`Upload progress: ${percentCompleted}%`);
        }
      }
    );

    console.log('Success:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
    throw error;
  }
};
```

### cURL

```bash
# 이미지 업로드
curl -X POST http://localhost:3000/api/images/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "image=@/path/to/image.jpg"

# FastAPI 헬스 체크
curl -X GET http://localhost:3000/api/images/health
```

---

## 환경 설정

### .env 파일

```env
# FastAPI 서버 URL
FASTAPI_URL=http://localhost:8000
```

### FastAPI 서버 요구사항

Node.js 서버가 다음 엔드포인트를 호출합니다:

**이미지 처리:**
- **Endpoint**: `POST /api/upload`
- **Request**: `multipart/form-data` (필드명: `file`)
- **Response**: JSON 형태의 처리 결과

**헬스 체크:**
- **Endpoint**: `GET /health`
- **Response**: 200 OK

---

## 파일 크기 제한 변경

파일 크기 제한을 변경하려면 `src/middlewares/upload.middleware.ts` 수정:

```typescript
export const upload = multer({
  storage: storage,
  fileFilter: fileFilter,
  limits: {
    fileSize: 20 * 1024 * 1024, // 20MB로 변경
  },
});
```

---

## 보안 고려사항

1. **파일 타입 검증**: 이미지 파일만 허용
2. **파일 크기 제한**: 10MB 제한
3. **인증 필수**: JWT 토큰 검증
4. **메모리 스토리지**: 파일을 디스크에 저장하지 않음 (보안↑)
5. **FastAPI 연동**: Node.js가 프록시 역할, 직접 노출 방지
