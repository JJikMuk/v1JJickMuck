import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import { userService } from '../services/user.service';

interface HomeProps {
  isAuthenticated?: boolean;
  userName?: string;
  onLogout?: () => void;
}

export default function Home({ isAuthenticated, userName, onLogout }: HomeProps) {
  const navigate = useNavigate();

  const handleStart = async () => {
    // 로그인하지 않은 경우 로그인 페이지로
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    // 로그인한 경우 프로필 확인
    try {
      const response = await userService.getProfile();

      if (response.success && response.data) {
        const user = response.data;

        // 알레르기나 식단 타입이 설정되지 않은 경우 설정 페이지로
        if (!user.diet_type || !user.allergies || user.allergies.length === 0) {
          navigate('/settings');
        } else {
          // 설정이 완료된 경우 업로드 페이지로
          navigate('/upload');
        }
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      // 에러 발생 시 설정 페이지로
      navigate('/settings');
    }
  };

  return (
    <div className="home-page">
      <Header
        onLogout={onLogout}
        userName={userName}
        onLogin={() => navigate('/login')}
        onSignup={() => navigate('/signup')}
        onProfile={() => navigate('/profile')}
        onDashboard={() => navigate('/dashboard')}
        isAuthenticated={isAuthenticated}
      />

      <main className="hero-section">
        <div className="hero-container">
          <div className="hero-content">
            <p className="hero-badge">음식 알레르기 검사</p>
            <h1 className="hero-title">
              음식 사진으로
              <br />
              알레르기 검사를
              <br />
              간편하게.
            </h1>
            <p className="hero-description">
              음식 사진을 업로드하면 AI가 자동으로 성분을 분석하여
              <br />
              알레르기 정보를 알려드립니다.
            </p>

            <div className="hero-buttons">
              <button onClick={handleStart} className="btn-primary">
                시작하기
              </button>
            </div>
          </div>

          <div className="hero-image">
            <div className="image-placeholder">
              <div className="placeholder-content">
                <span>🍽️</span>
                <p>안전한 식사를 위한 첫걸음</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      <section className="trusted-section">
        <p className="trusted-text">
          안전한 식생활을 위한 필수 서비스
        </p>
      </section>
    </div>
  );
}
