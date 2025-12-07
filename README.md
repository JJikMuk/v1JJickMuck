# v1JJickMuck - 식품 영양 정보 및 알레르기 분석 시스템

식품 라벨 이미지에서 영양 정보와 원재료를 자동으로 추출하고, 사용자의 건강 정보 및 알레르기를 고려하여 섭취 가능 여부를 분석하는 웹 애플리케이션입니다.

## 주요 기능

- **OCR 기반 정보 추출**: YOLO + EasyOCR을 활용하여 식품 라벨에서 영양 정보 및 원재료 자동 인식
- **알레르기 검사**: 사용자 알레르기 항목과 원재료 매칭을 통한 섭취 위험 알림
- **영양 정보 분석**: 개인의 건강 정보(키, 몸무게, 연령, 성별)를 기반으로 한 영양 섭취 분석
- **실시간 이미지 업로드**: 식품 사진을 촬영하거나 업로드하여 즉시 분석

## main.py : Yolo+OCR+RAG 실행시키는 코드
## nutrition_yolo, material_yolo : 검출용 코드
## NutritionImageToText : 추론 코드 및 보조 함수
## requirements.txt : 사용된 패키지 버전
 
## 기술 스택

### Backend (FastAPI)
- **FastAPI** - 고성능 비동기 웹 프레임워크
- **Ultralytics (YOLO)** - 영양 정보 및 원재료 영역 검출
- **EasyOCR** - 한글/영문 텍스트 인식
- **OpenCV** - 이미지 전처리 및 처리
- **PyTorch** - 딥러닝 모델 실행 환경

### Frontend
- **React 19** - 사용자 인터페이스
- **TypeScript** - 타입 안전성
- **Vite** - 빌드 도구 및 개발 서버
- **Axios** - HTTP 클라이언트
- **React Router** - 라우팅

## 프로젝트 구조

```
v1JJickMuck/
├── fastapi/                          # FastAPI 백엔드
│   ├── MaterialAndNutritionOCR/      # OCR 모듈
│   │   ├── MaterialImageToText.py    # 원재료 추출
│   │   ├── NutritionImageToText.py   # 영양 정보 추출
│   │   └── MaterialAndNutritionImageToText.py  # 통합 모듈
│   ├── main.py                       # FastAPI 엔트리포인트
│   ├── test_ocr.py                   # OCR 테스트 스크립트
│   └── requirements.txt              # Python 의존성
├── frontend/                         # React 프론트엔드
│   ├── src/
│   │   ├── components/               # React 컴포넌트
│   │   ├── pages/                    # 페이지 컴포넌트
│   │   └── styles/                   # CSS 스타일
│   └── package.json                  # Node.js 의존성
└── README.md
```

## 설치 및 실행 방법

### 1️⃣ 사전 요구사항

- **Python 3.10+**
- **Node.js 18+**
- **Git**

### 2️⃣ 프로젝트 클론

```bash
git clone <repository-url>
cd v1JJickMuck
```

### 3️⃣ Backend 설정 및 실행

#### Python 가상환경 생성 및 활성화

```bash
cd fastapi
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### 의존성 설치

```bash
pip install -r requirements.txt
```

#### YOLO 모델 파일 준비

프로젝트에서 사용하는 YOLO 모델 파일을 다음 위치에 배치해야 합니다:
- `MaterialAndNutritionOCR/nutrition_yolo.pt` (영양 정보 검출 모델)
- `MaterialAndNutritionOCR/material_yolo.pt` (원재료 검출 모델)

#### FastAPI 서버 실행

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 `http://localhost:8000`에서 API에 접근할 수 있습니다.

### 4️⃣ Frontend 설정 및 실행

새 터미널 창을 열어서 진행합니다.

```bash
cd frontend
npm install
npm run dev
```

프론트엔드 개발 서버가 실행되면 브라우저에서 `http://localhost:5173`으로 접속합니다.

### Nodejs 설정 및 실행
```bash
cd backend
npm install
npm run dev
```

## API 엔드포인트

### `POST /ocr`

식품 이미지를 업로드하여 영양 정보와 원재료를 추출합니다.

**요청:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `file` (이미지 파일)

**응답 예시:**
```json
{
  "status": "success",
  "nutrition": {
    "총내용량": [500, 0.95, 1.0],
    "kcal": ["300kcal", 0.98, 1.0],
    "나트륨": [450, 0.92, 0.85],
    "탄수화물": [60, 0.94, 0.88],
    "당류": [15, 0.91, 0.82],
    "지방": [10, 0.93, 0.87],
    "단백질": [8, 0.96, 0.90]
  },
  "material": ["밀", "우유", "대두"]
}
```

## 테스트

### Backend OCR 테스트

FastAPI 서버가 실행 중인 상태에서:

```bash
cd fastapi
python test_ocr.py
```

테스트 이미지 파일(`test_image.jpg`, `sample.png` 등)을 `fastapi` 폴더에 준비해야 합니다.

## 개발 환경

### Backend 개발

```bash
cd fastapi
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn main:app --reload
```

### Frontend 개발

```bash
cd frontend
npm run dev
```

### 빌드

Frontend 프로덕션 빌드:
```bash
cd frontend
npm run build
```

빌드된 파일은 `frontend/dist` 폴더에 생성됩니다.

## 주요 의존성

### Backend (Python)
- fastapi >= 0.100.0
- uvicorn >= 0.20.0
- ultralytics >= 8.0.0 (YOLO)
- easyocr >= 1.7.0
- opencv-python >= 4.8.0
- torch >= 2.0.0
- numpy >= 1.24.0
- matplotlib >= 3.7.0

### Frontend (Node.js)
- react ^19.2.0
- react-router-dom ^7.9.6
- axios ^1.13.2
- vite ^7.2.4
- typescript ~5.9.3

## 문제 해결

### YOLO 모델 로드 실패
- YOLO 모델 파일(`.pt`)이 올바른 경로에 있는지 확인
- PyTorch가 정상적으로 설치되었는지 확인

### EasyOCR 설치 오류
- 시스템에 충분한 메모리가 있는지 확인
- CUDA가 설치되어 있다면 PyTorch CUDA 버전 설치 확인

### CORS 오류
- FastAPI의 CORS 설정이 프론트엔드 주소를 허용하는지 확인
- 현재는 모든 origin(`*`)을 허용하도록 설정됨

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 개발되었습니다.
