# Frontend - React + Vite + TypeScript

## 📁 폴더 구조

```
frontend/
├── src/
│   ├── components/       # 재사용 가능한 UI 컴포넌트
│   ├── pages/           # 페이지 컴포넌트
│   ├── services/        # API 서비스 레이어
│   │   ├── api.ts           # 기본 API 설정 및 헬퍼
│   │   ├── auth.service.ts  # 인증 관련 API
│   │   ├── user.service.ts  # 사용자 관련 API
│   │   └── image.service.ts # 이미지 업로드 API
│   ├── hooks/           # 커스텀 React 훅
│   ├── contexts/        # React Context (전역 상태)
│   │   └── AuthContext.tsx  # 인증 컨텍스트
│   ├── types/           # TypeScript 타입 정의
│   │   └── index.ts         # 공통 타입
│   ├── utils/           # 유틸리티 함수
│   ├── assets/          # 정적 파일 (이미지, 폰트 등)
│   ├── App.tsx          # 메인 App 컴포넌트
│   └── main.tsx         # 엔트리 포인트
├── .env                 # 환경 변수
├── .env.example         # 환경 변수 예시
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 🚀 시작하기

### 1. 의존성 설치
```bash
cd frontend
npm install
```

### 2. 환경 변수 설정
`.env` 파일을 확인하고 필요시 수정:
```env
VITE_API_BASE_URL=http://localhost:3000/api
```

### 3. 개발 서버 실행
```bash
npm run dev
```

## 📦 주요 구성 요소

### Services
- **api.ts**: 공통 API 설정, 토큰 관리, fetch 헬퍼
- **auth.service.ts**: 회원가입, 로그인, 로그아웃, 토큰 갱신
- **user.service.ts**: 프로필 조회, 프로필 업데이트
- **image.service.ts**: 이미지 업로드, FastAPI 헬스체크

### Contexts
- **AuthContext**: 전역 인증 상태 관리 (user, isAuthenticated, login, logout)

### Types
- 백엔드 API와 일치하는 TypeScript 타입 정의
- `User`, `AuthResponse`, `ImageUploadResponse` 등

## 🛠 기술 스택

- **React 19**: UI 라이브러리
- **TypeScript**: 타입 안정성
- **Vite**: 빌드 도구
- **Context API**: 전역 상태 관리

## 📝 다음 단계

1. UI 컴포넌트 개발 (로그인, 회원가입, 이미지 업로드 등)
2. 페이지 컴포넌트 작성
3. 라우팅 설정 (React Router 설치 필요시)
4. 스타일링 (CSS/Tailwind/Material-UI 등)
