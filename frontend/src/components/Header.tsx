interface HeaderProps {
  onLogout?: () => void;
  userName?: string;
  onLogin?: () => void;
  onSignup?: () => void;
  onProfile?: () => void;
  onDashboard?: () => void;
  isAuthenticated?: boolean;
}

export default function Header({ onLogout, userName, onLogin, onSignup, onProfile, onDashboard, isAuthenticated }: HeaderProps) {
  return (
    <header className="header">
      <div className="header-container">
        <div className="logo">찍먹 Go</div>

        <nav className="nav">
          <a href="/" className="nav-link">Home</a>
          {isAuthenticated && (
            <a href="/dashboard" className="nav-link">대시보드</a>
          )}
          <a href="#about" className="nav-link">About us</a>
          <a href="#contact" className="nav-link">Contact</a>
        </nav>

        <div className="auth-buttons">
          {isAuthenticated ? (
            <>
              <span className="user-name">{userName}</span>
              <button onClick={onDashboard} className="btn-profile">
                대시보드
              </button>
              <button onClick={onProfile} className="btn-profile">
                프로필 수정
              </button>
              <button onClick={onLogout} className="btn-logout">
                Logout
              </button>
            </>
          ) : (
            <>
              <button onClick={onLogin} className="btn-login">Log in</button>
              <button onClick={onSignup} className="btn-signup">Sign up</button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
