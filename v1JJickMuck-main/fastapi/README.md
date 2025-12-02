# JJikMuk FastAPI RAG + LLM Server

식품 영양 분석을 위한 RAG(Retrieval-Augmented Generation) + LLM API 서버입니다.

## 📋 개요

### 아키텍처

```
Front → Node.js → FastAPI(OCR) → Node.js → FastAPI(RAG+LLM) → Node.js → Front
                                              ↑ 여기!
```

이 서버는 **RAG + LLM** 부분만 담당합니다. OCR은 별도 서비스에서 처리됩니다.

### 주요 기능

- **규칙 기반 분석**: PostgreSQL + pgvector를 활용한 규칙 매칭
- **RAG 검색**: 관련 영양/건강 지식 검색
- **GPT 분석**: OpenAI GPT를 활용한 개인화된 영양 조언

## 🚀 빠른 시작

### 1. PostgreSQL + pgvector 설치

```bash
# Docker로 PostgreSQL + pgvector 실행
docker run --name jjikmuk-postgres \
  -e POSTGRES_USER=jjikmuk \
  -e POSTGRES_PASSWORD=jjikmuk123 \
  -e POSTGRES_DB=jjikmuk \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16
```

### 2. 가상환경 설정

```bash
cd backend/fastapi
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정

```bash
# .env.example을 복사하여 .env 생성
cp .env.example .env

# .env 파일 편집
```

필수 환경변수:
```env
OPENAI_API_KEY=your-actual-openai-api-key
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=jjikmuk
POSTGRES_PASSWORD=jjikmuk123
POSTGRES_DB=jjikmuk
```

### 5. 데이터베이스 초기화 및 시드 데이터

```bash
# 시드 데이터 추가 (지식 베이스 + 분석 규칙)
python -m scripts.seed_data
```

### 6. 서버 실행

```bash
# 개발 모드 (자동 리로드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는
python -m app.main
```

## 📚 API 문서

서버 실행 후 아래 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔌 API 엔드포인트

### RAG + LLM 분석 (전체)

```http
POST /api/v1/rag/analyze
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  "user_id": "user-uuid",
  "product_data": {
    "product_name": "신라면",
    "nutritional_info": {
      "calories": 500,
      "carbohydrates": 78,
      "protein": 10,
      "fat": 16,
      "sodium": 1790,
      "sugar": 4
    },
    "ingredients": ["밀가루", "팜유", "소금"],
    "allergens": ["밀", "대두"]
  },
  "user_profile": {
    "height": 175,
    "weight": 70,
    "age_range": "20대",
    "allergies": ["땅콩"],
    "diseases": ["고혈압"]
  }
}
```

### 규칙 기반 분석만 (GPT 없이)

```http
POST /api/v1/rag/analyze-rule-only
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  # 동일한 요청 형식
}
```

### 응답 예시

```json
{
  "success": true,
  "analysis": {
    "suitability": "warning",
    "score": 55,
    "recommendations": [
      "⚠️ 고혈압 환자분께: 이 제품의 나트륨 함량이 높습니다. (1790mg)"
    ],
    "alternatives": [
      {
        "product_name": "저염 라면",
        "reason": "나트륨 함량이 낮습니다"
      }
    ],
    "nutritional_advice": "나트륨 섭취를 줄이기 위해 국물을 적게 드시는 것이 좋습니다.",
    "warnings": [
      {
        "type": "disease",
        "severity": "warning",
        "message": "고혈압 환자는 나트륨 섭취에 주의하세요",
        "affected_nutrient": "sodium"
      }
    ]
  },
  "rule_result": {
    "matched_rules": [...],
    "warnings": [...],
    "score_adjustments": -25,
    "base_score": 80,
    "final_score": 55
  }
}
```

## 🏗️ 프로젝트 구조

```
backend/fastapi/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 앱 진입점
│   ├── config/
│   │   └── settings.py      # 환경 설정
│   ├── database/
│   │   ├── __init__.py
│   │   └── models.py        # SQLAlchemy 모델 (pgvector)
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── rag.py       # RAG 분석 엔드포인트
│   ├── models/
│   │   ├── __init__.py
│   │   └── rag_models.py    # Pydantic 모델
│   └── services/
│       ├── __init__.py
│       ├── gpt_service.py   # GPT API 통합 서비스
│       └── rag_service.py   # RAG + 규칙 기반 서비스
├── scripts/
│   └── seed_data.py         # 시드 데이터 스크립트
├── requirements.txt
├── .env.example
└── README.md
```

## 🗄️ 데이터베이스 스키마

### knowledge_documents (지식 베이스)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | SERIAL | Primary Key |
| `content` | TEXT | 문서 내용 |
| `category` | VARCHAR(50) | allergies, diseases, nutrition |
| `title` | VARCHAR(200) | 문서 제목 |
| `keywords` | TEXT[] | 키워드 배열 |
| `embedding` | VECTOR(1536) | OpenAI 임베딩 벡터 |

### analysis_rules (분석 규칙)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | SERIAL | Primary Key |
| `rule_type` | VARCHAR(50) | allergy, disease, nutrition |
| `condition_key` | VARCHAR(100) | 조건 키 (예: "당뇨", "땅콩") |
| `nutrient_limits` | TEXT (JSON) | 영양소 제한 조건 |
| `warning_message` | TEXT | 경고 메시지 |
| `severity` | VARCHAR(20) | safe, warning, danger |
| `score_impact` | INTEGER | 점수 영향도 |

## 🔑 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 키 | (필수) |
| `OPENAI_MODEL` | 사용할 GPT 모델 | `gpt-4-turbo-preview` |
| `POSTGRES_HOST` | PostgreSQL 호스트 | `localhost` |
| `POSTGRES_PORT` | PostgreSQL 포트 | `5432` |
| `POSTGRES_USER` | PostgreSQL 사용자 | `jjikmuk` |
| `POSTGRES_PASSWORD` | PostgreSQL 비밀번호 | (필수) |
| `POSTGRES_DB` | PostgreSQL 데이터베이스 | `jjikmuk` |
| `HOST` | 서버 호스트 | `0.0.0.0` |
| `PORT` | 서버 포트 | `8000` |
| `API_KEY` | API 인증 키 | `temporary-key` |

## 🔄 Node.js와의 연동

Node.js 미들웨어에서 이 FastAPI 서버를 호출합니다:

```typescript
// backend/nodeJs/src/services/fastapi.service.ts

const FASTAPI_RAG_URL = process.env.FASTAPI_RAG_URL || "http://localhost:8000";

// RAG + LLM 분석 호출
const response = await axios.post(`${FASTAPI_RAG_URL}/api/v1/rag/analyze`, {
  user_id: userId,
  product_data: productData,
  user_profile: userProfile
}, {
  headers: {
    'Authorization': `Bearer ${process.env.FASTAPI_API_KEY}`
  }
});
```

## 🧪 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# RAG 분석 테스트
curl -X POST http://localhost:8000/api/v1/rag/analyze \
  -H "Authorization: Bearer temporary-key" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "product_data": {
      "product_name": "테스트 과자",
      "nutritional_info": {
        "calories": 250,
        "sodium": 500,
        "sugar": 15
      },
      "allergens": ["우유"]
    },
    "user_profile": {
      "allergies": ["땅콩"],
      "diseases": ["당뇨"]
    }
  }'

# 규칙 기반 분석만 테스트
curl -X POST http://localhost:8000/api/v1/rag/analyze-rule-only \
  -H "Authorization: Bearer temporary-key" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "product_data": {
      "nutritional_info": {"sodium": 1800},
      "allergens": []
    },
    "user_profile": {
      "diseases": ["고혈압"]
    }
  }'
```

## 📝 라이선스

MIT License
