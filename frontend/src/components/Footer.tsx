import '../styles/footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      {/* Sponsor Section */}
      <section className="sponsors-section">
        <div className="container">
          <h2 className="sponsors-title">후원사</h2>
          <p className="sponsors-subtitle">안전한 식생활을 함께 만들어가는 파트너들</p>

          <div className="sponsors-grid">
            <div className="sponsor-card">
              <div className="sponsor-logo aws-logo">
                <img
                  src="https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg"
                  alt="AWS Logo"
                />
              </div>
              <h3>Amazon Web Services</h3>
              <p>클라우드 인프라 파트너</p>
            </div>

            <div className="sponsor-card">
              <div className="sponsor-logo aws-logo">
                <img
                  src="https://upload.wikimedia.org/wikipedia/commons/4/4b/Cloudflare_Logo.svg"
                  alt="Cloudflare Logo"
                />
              </div>
              <h3>Cloudflare</h3>
              <p>클라우드 인프라 파트너</p>
            </div>

            <div className="sponsor-card">
              <div className="sponsor-logo aws-logo">
                <img
                  src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg"
                  alt="Google Logo"
                />
              </div>
              <h3>Google</h3>
              <p>기술 지원 파트너</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer Content */}
      <div className="footer-content">
        <div className="container">
          <div className="footer-grid">
            {/* About */}
            <div className="footer-column">
              <h3 className="footer-heading">알레르기 검사</h3>
              <p className="footer-description">
                AI 기반 음식 알레르기 분석 서비스로
                안전한 식생활을 지원합니다.
              </p>
            </div>

            {/* Links */}
            <div className="footer-column">
              <h4 className="footer-title">서비스</h4>
              <ul className="footer-links">
                <li><a href="/upload">알레르기 검사</a></li>
                <li><a href="/dashboard">대시보드</a></li>
                <li><a href="/settings">설정</a></li>
              </ul>
            </div>

            {/* Company */}
            <div className="footer-column">
              <h4 className="footer-title">회사</h4>
              <ul className="footer-links">
                <li><a href="/about">회사 소개</a></li>
                <li><a href="/contact">문의하기</a></li>
                <li><a href="/careers">채용</a></li>
              </ul>
            </div>

            {/* Legal */}
            <div className="footer-column">
              <h4 className="footer-title">법적 고지</h4>
              <ul className="footer-links">
                <li><a href="/privacy">개인정보처리방침</a></li>
                <li><a href="/terms">이용약관</a></li>
                <li><a href="/disclaimer">면책조항</a></li>
              </ul>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="footer-bottom">
            <p className="copyright">
              © 2025 알레르기 검사. All rights reserved.
            </p>
            <div className="social-links">
              <a href="#" aria-label="Facebook">📘</a>
              <a href="#" aria-label="Twitter">🐦</a>
              <a href="#" aria-label="Instagram">📷</a>
              <a href="#" aria-label="LinkedIn">💼</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
