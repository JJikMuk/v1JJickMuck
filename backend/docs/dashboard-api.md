# Dashboard API 문서

## 개요
사용자의 스캔 히스토리를 기반으로 통계 및 히스토리를 제공하는 API입니다.

## 인증
모든 API는 JWT 인증이 필요합니다.
- Header: `Authorization: Bearer {token}`

---

## 1. 대시보드 통계 조회

**Endpoint:** `GET /api/dashboard/stats`

**Query Parameters:**
- `period` (optional): `week` | `month` | `all` (기본값: `week`)

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "scan_count": 45,
    "risk_distribution": {
      "green": 30,
      "yellow": 10,
      "red": 5
    },
    "allergen_frequency": {
      "땅콩": 8,
      "유제품": 5,
      "계란": 3
    },
    "diet_violation_count": 7,
    "avg_nutrition": {
      "calories": "245.5",
      "carbs": "35.2",
      "protein": "8.1",
      "fat": "12.3"
    }
  }
}
```

---

## 2. 스캔 히스토리 목록 조회

**Endpoint:** `GET /api/dashboard/history`

**Query Parameters:**
- `period` (optional): `week` | `month` | `all` (기본값: `week`)

**응답 예시:**
```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "user_id": 1,
      "product_name": "초코파이",
      "risk_level": "yellow",
      "risk_score": 50,
      "risk_reason": "유제품 포함 - 비건 부적합",
      "calories": 120.5,
      "carbs": 25.3,
      "protein": 2.1,
      "fat": 5.8,
      "detected_ingredients": ["밀가루", "설탕", "유제품"],
      "detected_allergens": ["유제품"],
      "diet_warnings": ["유제품 포함 - 비건 부적합"],
      "scanned_at": "2025-11-30T10:30:00.000Z"
    }
  ]
}
```

---

## 데이터 흐름

1. **이미지 업로드 시** (`POST /api/images/upload`)
   - FastAPI로 OCR 요청
   - 응답받은 데이터를 `SCAN_HISTORY` 테이블에 자동 저장

2. **대시보드 조회 시**
   - 저장된 히스토리를 기반으로 통계 계산
   - 기간별 필터링 지원 (7일, 30일, 전체)

---

## 테이블 구조

### SCAN_HISTORY
```sql
- id: 히스토리 ID
- user_id: 사용자 ID
- product_name: 제품명
- risk_level: 위험도 (green/yellow/red)
- risk_score: 위험도 점수 (0-100)
- risk_reason: 위험도 판단 이유
- calories, carbs, protein, fat: 영양 정보
- detected_ingredients: 검출된 원재료 (JSON)
- detected_allergens: 검출된 알레르기 성분 (JSON)
- diet_warnings: 식단 위반 사항 (JSON)
- ocr_full_result: FastAPI 전체 응답 (JSON)
- scanned_at: 스캔 일시
```
