import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Home from './pages/Home';
import Settings from './pages/Settings';
import Profile from './pages/Profile';
import Upload from './pages/Upload';
import Dashboard from './pages/Dashboard';
import './styles/auth.css';
import './styles/home.css';
import './styles/settings.css';
import './styles/profile.css';
import './styles/upload.css';
import './styles/dashboard.css';

function AppRoutes() {
  const { isAuthenticated, isLoading, user, logout } = useAuth();

  // Show loading screen while checking authentication
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh'
      }}>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <Routes>
      {/* Home - Landing Page */}
      <Route
        path="/"
        element={
          <Home
            isAuthenticated={isAuthenticated}
            userName={user?.name}
            onLogout={logout}
          />
        }
      />

      {/* Login Page */}
      <Route path="/login" element={<Login />} />

      {/* Signup Page */}
      <Route path="/signup" element={<Signup />} />

      {/* Settings Page */}
      <Route path="/settings" element={<Settings />} />

      {/* Profile Page */}
      <Route path="/profile" element={<Profile />} />

      {/* Upload Page */}
      <Route path="/upload" element={<Upload />} />

      {/* Dashboard Page */}
      <Route path="/dashboard" element={<Dashboard />} />

      {/* Catch all - redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
