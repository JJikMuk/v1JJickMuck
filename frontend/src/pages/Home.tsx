import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { userService } from '../services/user.service';

interface HomeProps {
  isAuthenticated?: boolean;
  userName?: string;
  onLogout?: () => void;
}

export default function Home({ isAuthenticated, userName, onLogout }: HomeProps) {
  const navigate = useNavigate();
  const [currentSlide, setCurrentSlide] = useState(0);

  // 이미지 슬라이더 데이터
  const slides = [
    {
      icon: '🍽️',
      title: '안전한 식사를 위한 첫걸음 시작하기',
      bgColor: '#E3F2FD',
      action: 'start'
    },
    {
      icon: '🏢',
      title: '여러 후원사들과 함께합니다',
      bgColor: '#F1F8E9',
      action: 'sponsors'
    }
  ];

  // 자동 슬라이드
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
    }, 3000); // 3초마다 전환

    return () => clearInterval(timer);
  }, [slides.length]);

  const scrollToSponsors = () => {
    const sponsorsSection = document.querySelector('.sponsors-section');
    if (sponsorsSection) {
      sponsorsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleSlideClick = async (action: string) => {
    if (action === 'sponsors') {
      scrollToSponsors();
      return;
    }

    // 'start' action
    // 로그인하지 않은 경우 로그인 페이지로
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    // 로그인한 경우 프로필 확인
    try {
      const response = await userService.getFullProfile();

      if (response.success && response.data) {
        const user = response.data;

        // 모든 필수 정보가 설정되어 있는지 확인
        const hasHealthInfo = user.height && user.weight && user.age_range && user.gender;
        const hasAllergyOrDiet = user.diet_type || (user.allergies && user.allergies.length > 0);

        if (hasHealthInfo && hasAllergyOrDiet) {
          // 모든 설정이 완료된 경우 업로드 페이지로
          navigate('/upload');
        } else if (!hasHealthInfo) {
          // 신체 정보가 없으면 첫 번째 설정 페이지로
          navigate('/health-settings');
        } else {
          // 신체 정보는 있지만 알레르기/식단 정보가 없으면
          navigate('/settings');
        }
      } else {
        // 프로필 조회 실패 시 첫 번째 설정 페이지로
        navigate('/health-settings');
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      // 에러 발생 시 첫 번째 설정 페이지로
      navigate('/health-settings');
    }
  };

  const handleStart = () => handleSlideClick('start');

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
            <div className="image-slider">
              <div className="slider-container">
                {slides.map((slide, index) => (
                  <div
                    key={index}
                    className={`slide ${index === currentSlide ? 'active' : ''}`}
                    style={{ backgroundColor: slide.bgColor }}
                    onClick={() => handleSlideClick(slide.action)}
                  >
                    <div className="slide-content">
                      <span className="slide-icon">{slide.icon}</span>
                      <p className="slide-title">{slide.title}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* 인디케이터 */}
              <div className="slider-indicators">
                {slides.map((_, index) => (
                  <button
                    key={index}
                    className={`indicator ${index === currentSlide ? 'active' : ''}`}
                    onClick={() => setCurrentSlide(index)}
                    aria-label={`슬라이드 ${index + 1}`}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>

      <section className="trusted-section">
        <button className="scroll-down-button" onClick={scrollToSponsors} aria-label="스크롤 다운">
          <div className="scroll-arrow">
            <span>⌄</span>
            <span>⌄</span>
            <span>⌄</span>
          </div>
        </button>
      </section>

      <Footer />
    </div>
  );
}
