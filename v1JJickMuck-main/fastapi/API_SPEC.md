# JJikMuk FastAPI RAG + LLM API 명세서

> **Node.js 서버에서 호출하는 FastAPI 엔드포인트 명세**

## 📌 기본 정보

| 항목 | 값 |
|------|-----|
| Base URL | `http://localhost:8000` |
| API Version | `v1` |
| Content-Type | `application/json` |
| 인증 방식 | Bearer Token |

---

## 🔐 인증

모든 API 요청에는 `Authorization` 헤더가 필요합니다.

```
Authorization: Bearer <API_KEY>
```

**예시:**
```javascript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${process.env.FASTAPI_API_KEY}`
};
```

---

## 📡 엔드포인트

### 1. 제품 분석 (RAG + GPT)

OCR로 파싱된 제품 정보와 사용자 프로필을 기반으로 종합 분석을 수행합니다.

#### `POST /api/v1/rag/analyze`

**Request Body:**
```json
{
  "userId": "string",
  "productData": {
    "productName": "string | null",
    "nutritionalInfo": {
      "calories": "number | null",
      "carbohydrates": "number | null",
      "protein": "number | null",
      "fat": "number | null",
      "sodium": "number | null",
      "sugar": "number | null",
      "fiber": "number | null",
      "cholesterol": "number | null",
      "saturatedFat": "number | null",
      "transFat": "number | null"
    },
    "ingredients": ["string"],
    "allergens": ["string"]
  },
  "userProfile": {
    "height": "number | null",
    "weight": "number | null",
    "ageRange": "string | null",
    "gender": "male | female | other | null",
    "allergies": ["string"],
    "diseases": ["string"],
    "specialConditions": ["string"]
  }
}
```

**Response (Success):**
```json
{
  "success": true,
  "analysis": {
    "suitability": "safe | warning | danger",
    "score": 85,
    "recommendations": [
      "이 제품은 나트륨 함량이 적어 고혈압 환자에게 적합합니다.",
      "단백질 함량이 높아 근육 유지에 도움이 됩니다."
    ],
    "alternatives": [
      {
        "productName": "저염 두부",
        "reason": "나트륨 함량이 50% 낮습니다."
      }
    ],
    "nutritionalAdvice": "하루 권장 나트륨 섭취량의 15%에 해당합니다. 다른 식사에서 나트륨 섭취를 조절하세요."
  }
}
```

**Response (Error):**
```json
{
  "success": false,
  "analysis": null,
  "error": "에러 메시지"
}
```

---

### 2. 규칙 기반 분석 (GPT 없이)

GPT API를 사용하지 않고 PostgreSQL 규칙만으로 빠르게 분석합니다.

#### `POST /api/v1/rag/analyze-rule-only`

**Request Body:** `/api/v1/rag/analyze`와 동일

**Response:** `/api/v1/rag/analyze`와 동일

**사용 케이스:**
- GPT API 사용량 제한 시
- 빠른 응답이 필요한 경우
- 테스트 목적

---

### 3. RAG 서비스 상태 확인

#### `GET /api/v1/rag/health`

**Response:**
```json
{
  "status": "healthy",
  "service": "RAG + LLM Analysis",
  "version": "1.0.0",
  "database": "PostgreSQL + pgvector"
}
```

---

### 4. 서버 상태 확인

#### `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "JJikMuk RAG + LLM API",
  "version": "1.0.0",
  "database": "PostgreSQL + pgvector"
}
```

---

## 📊 데이터 타입 상세

### Suitability (적합성 수준)

| 값 | 설명 | 점수 범위 |
|-----|------|----------|
| `safe` | 안전 - 섭취 권장 | 70-100 |
| `warning` | 주의 - 섭취 가능하나 주의 필요 | 40-69 |
| `danger` | 위험 - 섭취 비권장 | 0-39 |

### 알레르기 항목 (allergies)

```javascript
const ALLERGY_TYPES = [
  "우유", "계란", "땅콩", "대두", "밀",
  "고등어", "게", "새우", "돼지고기", "복숭아",
  "토마토", "아황산류", "호두", "닭고기", "쇠고기",
  "오징어", "조개류", "잣"
];
```

### 질병/건강상태 (diseases)

```javascript
const DISEASE_TYPES = [
  "당뇨병", "고혈압", "고지혈증", "신장질환",
  "심장질환", "통풍", "비만", "골다공증"
];
```

### 특수 상태 (specialConditions)

```javascript
const SPECIAL_CONDITIONS = [
  "임신", "수유중", "채식주의자", "비건"
];
```

---

## 💻 Node.js 호출 예시

### Axios 사용

```javascript
const axios = require('axios');

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';
const API_KEY = process.env.FASTAPI_API_KEY;

async function analyzeProduct(userId, productData, userProfile) {
  try {
    const response = await axios.post(
      `${FASTAPI_URL}/api/v1/rag/analyze`,
      {
        userId,
        productData,
        userProfile
      },
      {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${API_KEY}`
        },
        timeout: 30000 // GPT 응답 대기
      }
    );

    if (response.data.success) {
      return response.data.analysis;
    } else {
      throw new Error(response.data.error);
    }
  } catch (error) {
    console.error('FastAPI 분석 실패:', error.message);
    throw error;
  }
}

// 사용 예시
const result = await analyzeProduct(
  'user123',
  {
    productName: '신라면',
    nutritionalInfo: {
      calories: 500,
      sodium: 1800,
      sugar: 4
    },
    allergens: ['밀', '대두', '계란']
  },
  {
    allergies: ['계란'],
    diseases: ['고혈압'],
    ageRange: '30대',
    gender: 'male'
  }
);

console.log(result);
// {
//   suitability: 'danger',
//   score: 25,
//   recommendations: [...],
//   alternatives: [...],
//   nutritionalAdvice: '...'
// }
```

### Fetch 사용

```javascript
async function analyzeProduct(userId, productData, userProfile) {
  const response = await fetch(`${FASTAPI_URL}/api/v1/rag/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${API_KEY}`
    },
    body: JSON.stringify({
      userId,
      productData,
      userProfile
    })
  });

  const data = await response.json();
  
  if (!data.success) {
    throw new Error(data.error);
  }
  
  return data.analysis;
}
```

---

## ⚠️ 에러 코드

| HTTP Status | 설명 |
|-------------|------|
| 200 | 성공 (success: true/false 확인 필요) |
| 401 | 인증 실패 (API 키 오류) |
| 422 | 요청 데이터 검증 실패 |
| 500 | 서버 내부 오류 |

### 401 Unauthorized

```json
{
  "detail": "Authorization header required"
}
```
또는
```json
{
  "detail": "Invalid API key"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "userId"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 🔄 처리 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│                         Node.js Server                          │
├─────────────────────────────────────────────────────────────────┤
│  1. 프론트엔드로부터 제품 이미지 수신                              │
│  2. OCR FastAPI로 이미지 전송 → 영양정보 파싱                      │
│  3. DB에서 사용자 프로필 조회                                      │
│  4. RAG FastAPI로 분석 요청 ← 현재 API                            │
│  5. 분석 결과를 프론트엔드에 전달                                  │
└─────────────────────────────────────────────────────────────────┘

           │
           ▼ POST /api/v1/rag/analyze

┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI RAG Server                         │
├─────────────────────────────────────────────────────────────────┤
│  1. 사용자 알레르기/질병 기반 규칙 조회 (PostgreSQL)                │
│  2. 규칙 적용하여 위험/경고 판단                                   │
│  3. RAG로 관련 지식 검색 (pgvector)                               │
│  4. GPT로 맞춤형 분석 생성                                        │
│  5. 결과 반환                                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 참고사항

1. **타임아웃 설정**: GPT 분석은 최대 30초 소요될 수 있으므로 적절한 타임아웃 설정 필요
2. **Fallback**: GPT 실패 시 규칙 기반 분석 결과로 자동 대체됨
3. **camelCase**: 모든 요청/응답 필드는 camelCase 사용
4. **null 허용**: 대부분의 필드는 null 허용 (필수: userId, productData, userProfile)

---

## 🧪 테스트

### 헬스 체크
```bash
curl http://localhost:8000/health
```

### 분석 테스트
```bash
curl -X POST http://localhost:8000/api/v1/rag/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "userId": "test-user",
    "productData": {
      "productName": "테스트 제품",
      "nutritionalInfo": {
        "calories": 500,
        "sodium": 1000
      },
      "allergens": ["우유", "계란"]
    },
    "userProfile": {
      "allergies": ["계란"],
      "diseases": ["고혈압"]
    }
  }'
```

---

**문서 버전**: 1.0.0  
**최종 수정일**: 2025-12-02
