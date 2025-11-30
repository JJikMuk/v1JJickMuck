# 찍먹 Go - FastAPI 서버

음식 이미지 분석 및 알레르기 검사를 위한 FastAPI 백엔드 서버입니다.

## 기능

- **Gemini OCR**: 음식 이미지에서 성분 텍스트 추출
- **알레르기 분석**: 사용자의 알레르기 정보와 매칭하여 위험도 분석
- **식단 타입 검증**: 채식, 비건 등 식단 타입과 맞지 않는 성분 탐지
- **위험도 평가**: 3단계 신호등 시스템 (🔴 위험 / 🟡 주의 / 🟢 안전)

## 설치 및 실행

### 1. 패키지 설치

```bash
cd fastapi
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 Gemini API 키를 설정하세요:

```bash
cp .env.example .env
# .env 파일을 열어서 GEMINI_API_KEY를 입력하세요
```

Gemini API 키는 [Google AI Studio](https://makersuite.google.com/app/apikey)에서 발급받을 수 있습니다.

### 3. 서버 실행

```bash
python main.py
```

또는

```bash
uvicorn main:app --reload --port 8000
```

서버는 `http://localhost:8000`에서 실행됩니다.

## API 엔드포인트

### POST /api/upload

음식 이미지를 업로드하고 알레르기 분석 결과를 받습니다.

**요청:**
- `file`: 이미지 파일 (multipart/form-data)
- `user_info`: 사용자 정보 JSON 문자열
  ```json
  {
    "diet_type": "vegan",
    "allergies": ["땅콩", "우유"]
  }
  ```

**응답:**
```json
{
  "status": "success",
  "risk_level": "red",
  "risk_score": 85,
  "analysis": {
    "detected_ingredients": ["우유", "계란", "땅콩"],
    "allergen_warnings": [
      {
        "allergen": "땅콩",
        "severity": "high",
        "message": "사용자의 알레르기 항목에 포함되어 있습니다."
      }
    ],
    "diet_warnings": [
      {
        "ingredient": "계란",
        "reason": "비건 식단에 적합하지 않습니다."
      }
    ]
  },
  "recommendation": "이 음식은 땅콩 알레르기가 있는 분께 위험할 수 있습니다.",
  "ocr_text": "원재료: 우유, 계란, 땅콩..."
}
```

### GET /health

서버 상태 확인

**응답:**
```json
{
  "status": "healthy"
}
```

## 기술 스택

- **FastAPI**: 고성능 Python 웹 프레임워크
- **Google Gemini AI**: 이미지 분석 및 텍스트 생성
- **Pillow**: 이미지 처리
- **Uvicorn**: ASGI 서버

## 개발 로드맵

- [ ] RAG (Retrieval-Augmented Generation) 구현
- [ ] 벡터 데이터베이스 연동 (알레르기 정보 저장)
- [ ] 분석 결과 캐싱
- [ ] 다국어 지원

## 라이선스

MIT
