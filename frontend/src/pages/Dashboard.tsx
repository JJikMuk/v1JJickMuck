import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { dashboardApi } from '../services/api';
import Header from '../components/Header';

type Period = 'week' | 'month' | 'all';

interface DashboardStats {
  scan_count: number;
  risk_distribution: {
    green: number;
    yellow: number;
    red: number;
  };
  allergen_frequency: { [key: string]: number };
  diet_violation_count: number;
  avg_nutrition: {
    calories: string;
    carbs: string;
    protein: string;
    fat: string;
  };
}

interface ScanHistory {
  id: number;
  product_name: string;
  risk_level: 'green' | 'yellow' | 'red';
  risk_score: number;
  risk_reason: string;
  calories?: number;
  carbs?: number;
  protein?: number;
  fat?: number;
  detected_ingredients?: string[];
  detected_allergens?: string[];
  diet_warnings?: string[];
  scanned_at: string;
}

function Dashboard() {
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuth();
  const [period, setPeriod] = useState<Period>('week');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [history, setHistory] = useState<ScanHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    fetchDashboardData();
  }, [isAuthenticated, period]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsData, historyData] = await Promise.all([
        dashboardApi.getStats(period),
        dashboardApi.getHistory(period),
      ]);
      setStats(statsData);
      setHistory(historyData);
    } catch (err) {
      setError('대시보드 데이터를 불러오는데 실패했습니다.');
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevelLabel = (level: 'green' | 'yellow' | 'red') => {
    switch (level) {
      case 'green': return '안전';
      case 'yellow': return '주의';
      case 'red': return '위험';
    }
  };

  const getRiskLevelColor = (level: 'green' | 'yellow' | 'red') => {
    switch (level) {
      case 'green': return '#4CAF50';
      case 'yellow': return '#FFC107';
      case 'red': return '#F44336';
    }
  };

  const getPeriodLabel = (p: Period) => {
    switch (p) {
      case 'week': return '최근 7일';
      case 'month': return '최근 30일';
      case 'all': return '전체';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <Header
          isAuthenticated={isAuthenticated}
          userName={user?.name}
          onLogout={logout}
        />
        <div className="loading">데이터를 불러오는 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-container">
        <Header
          isAuthenticated={isAuthenticated}
          userName={user?.name}
          onLogout={logout}
        />
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <Header
        isAuthenticated={isAuthenticated}
        userName={user?.name}
        onLogout={logout}
      />

      <main className="dashboard-main">
        <div className="dashboard-header">
          <h1>나의 식품 스캔 통계</h1>
          <div className="period-selector">
            <button
              className={period === 'week' ? 'active' : ''}
              onClick={() => setPeriod('week')}
            >
              최근 7일
            </button>
            <button
              className={period === 'month' ? 'active' : ''}
              onClick={() => setPeriod('month')}
            >
              최근 30일
            </button>
            <button
              className={period === 'all' ? 'active' : ''}
              onClick={() => setPeriod('all')}
            >
              전체
            </button>
          </div>
        </div>

        {stats && (
          <>
            {/* Summary Cards */}
            <div className="stats-summary">
              <div className="stat-card">
                <div className="stat-icon">📊</div>
                <div className="stat-value">{stats.scan_count}</div>
                <div className="stat-label">총 스캔</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">✅</div>
                <div className="stat-value">
                  {stats.scan_count > 0
                    ? Math.round((stats.risk_distribution.green / stats.scan_count) * 100)
                    : 0}%
                </div>
                <div className="stat-label">안전 비율</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">⚠️</div>
                <div className="stat-value">{stats.risk_distribution.red}</div>
                <div className="stat-label">위험 제품</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🚫</div>
                <div className="stat-value">{stats.diet_violation_count}</div>
                <div className="stat-label">식단 위반</div>
              </div>
            </div>

            {/* Risk Distribution */}
            <div className="dashboard-section">
              <h2>위험도 분포</h2>
              <div className="risk-distribution">
                <div className="risk-bar">
                  <div
                    className="risk-segment green"
                    style={{
                      width: stats.scan_count > 0
                        ? `${(stats.risk_distribution.green / stats.scan_count) * 100}%`
                        : '0%'
                    }}
                  />
                  <div
                    className="risk-segment yellow"
                    style={{
                      width: stats.scan_count > 0
                        ? `${(stats.risk_distribution.yellow / stats.scan_count) * 100}%`
                        : '0%'
                    }}
                  />
                  <div
                    className="risk-segment red"
                    style={{
                      width: stats.scan_count > 0
                        ? `${(stats.risk_distribution.red / stats.scan_count) * 100}%`
                        : '0%'
                    }}
                  />
                </div>
                <div className="risk-legend">
                  <div className="legend-item">
                    <span className="legend-color green"></span>
                    <span>안전 {stats.risk_distribution.green}개 ({stats.scan_count > 0 ? Math.round((stats.risk_distribution.green / stats.scan_count) * 100) : 0}%)</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-color yellow"></span>
                    <span>주의 {stats.risk_distribution.yellow}개 ({stats.scan_count > 0 ? Math.round((stats.risk_distribution.yellow / stats.scan_count) * 100) : 0}%)</span>
                  </div>
                  <div className="legend-item">
                    <span className="legend-color red"></span>
                    <span>위험 {stats.risk_distribution.red}개 ({stats.scan_count > 0 ? Math.round((stats.risk_distribution.red / stats.scan_count) * 100) : 0}%)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Allergen Frequency */}
            {Object.keys(stats.allergen_frequency).length > 0 && (
              <div className="dashboard-section">
                <h2>자주 발견된 알레르기 성분</h2>
                <div className="allergen-list">
                  {Object.entries(stats.allergen_frequency)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 5)
                    .map(([allergen, count]) => (
                      <div key={allergen} className="allergen-item">
                        <span className="allergen-name">{allergen}</span>
                        <div className="allergen-bar-container">
                          <div
                            className="allergen-bar"
                            style={{
                              width: `${(count / Math.max(...Object.values(stats.allergen_frequency))) * 100}%`
                            }}
                          />
                        </div>
                        <span className="allergen-count">{count}회</span>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Average Nutrition */}
            <div className="dashboard-section">
              <h2>평균 영양 정보</h2>
              <div className="nutrition-grid">
                <div className="nutrition-card">
                  <div className="nutrition-label">열량</div>
                  <div className="nutrition-value">{stats.avg_nutrition.calories} kcal</div>
                </div>
                <div className="nutrition-card">
                  <div className="nutrition-label">탄수화물</div>
                  <div className="nutrition-value">{stats.avg_nutrition.carbs} g</div>
                </div>
                <div className="nutrition-card">
                  <div className="nutrition-label">단백질</div>
                  <div className="nutrition-value">{stats.avg_nutrition.protein} g</div>
                </div>
                <div className="nutrition-card">
                  <div className="nutrition-label">지방</div>
                  <div className="nutrition-value">{stats.avg_nutrition.fat} g</div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Scan History */}
        <div className="dashboard-section">
          <h2>스캔 기록</h2>
          {history.length === 0 ? (
            <div className="empty-state">
              <p>{getPeriodLabel(period)} 동안 스캔 기록이 없습니다.</p>
              <button onClick={() => navigate('/upload')}>첫 스캔 시작하기</button>
            </div>
          ) : (
            <div className="history-list">
              {history.map((item) => (
                <div key={item.id} className="history-item">
                  <div className="history-header">
                    <h3>{item.product_name}</h3>
                    <span
                      className="risk-badge"
                      style={{ backgroundColor: getRiskLevelColor(item.risk_level) }}
                    >
                      {getRiskLevelLabel(item.risk_level)}
                    </span>
                  </div>
                  <div className="history-date">{formatDate(item.scanned_at)}</div>
                  <div className="history-reason">{item.risk_reason}</div>
                  {item.detected_allergens && item.detected_allergens.length > 0 && (
                    <div className="history-allergens">
                      <strong>검출된 알레르기:</strong> {item.detected_allergens.join(', ')}
                    </div>
                  )}
                  {item.calories && (
                    <div className="history-nutrition">
                      열량: {item.calories}kcal | 탄: {item.carbs}g | 단: {item.protein}g | 지: {item.fat}g
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default Dashboard;
