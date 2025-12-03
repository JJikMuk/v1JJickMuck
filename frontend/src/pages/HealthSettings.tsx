import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { userService } from '../services/user.service';
import '../styles/settings.css';

const ageRanges = [
  { value: '10대', label: '10대' },
  { value: '20대', label: '20대' },
  { value: '30대', label: '30대' },
  { value: '40대', label: '40대' },
  { value: '50대', label: '50대' },
  { value: '60대 이상', label: '60대 이상' },
];

const genders = [
  { value: 'male', label: '남성' },
  { value: 'female', label: '여성' },
  { value: 'other', label: '기타' },
];

export default function HealthSettings() {
  const navigate = useNavigate();
  const [height, setHeight] = useState<string>('');
  const [weight, setWeight] = useState<string>('');
  const [ageRange, setAgeRange] = useState<string>('');
  const [gender, setGender] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const response = await userService.getFullProfile();
      if (response.success && response.data) {
        const user = response.data;
        if (user.height) setHeight(user.height.toString());
        if (user.weight) setWeight(user.weight.toString());
        if (user.age_range) setAgeRange(user.age_range);
        if (user.gender) setGender(user.gender);
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = async () => {
    setSaving(true);
    try {
      const response = await userService.updateHealthProfile({
        height: height ? parseFloat(height) : undefined,
        weight: weight ? parseFloat(weight) : undefined,
        age_range: ageRange || undefined,
        gender: gender || undefined,
      });

      if (response.success) {
        // 다음 페이지 (질병/특수 상태 설정)로 이동
        navigate('/health-conditions');  // /settings → /health-conditions
      } else {
        alert('저장 실패: ' + response.message);
      }
    } catch (error) {
      console.error('Save error:', error);
      alert('저장 중 오류가 발생했습니다.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="settings-page">
        <div className="loading">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="settings-page">
      <div className="settings-container">
        <div className="settings-header">
          <h1>신체 정보 설정</h1>
          <p>맞춤형 분석을 위해 신체 정보를 입력해주세요.</p>
        </div>

        <div className="settings-section">
          <h2>신체 정보</h2>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="height">키 (cm)</label>
              <input
                type="number"
                id="height"
                value={height}
                onChange={(e) => setHeight(e.target.value)}
                placeholder="170"
                min="100"
                max="250"
              />
            </div>
            <div className="form-group">
              <label htmlFor="weight">몸무게 (kg)</label>
              <input
                type="number"
                id="weight"
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                placeholder="65"
                min="20"
                max="300"
              />
            </div>
          </div>
        </div>

        <div className="settings-section">
          <h2>연령대</h2>
          <div className="option-grid">
            {ageRanges.map((age) => (
              <label key={age.value} className="option-item">
                <input
                  type="radio"
                  name="age_range"
                  value={age.value}
                  checked={ageRange === age.value}
                  onChange={(e) => setAgeRange(e.target.value)}
                />
                <span>{age.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="settings-section">
          <h2>성별</h2>
          <div className="option-grid">
            {genders.map((g) => (
              <label key={g.value} className="option-item">
                <input
                  type="radio"
                  name="gender"
                  value={g.value}
                  checked={gender === g.value}
                  onChange={(e) => setGender(e.target.value)}
                />
                <span>{g.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="settings-actions">
          <button
            onClick={handleNext}
            disabled={saving}
            className="btn-save"
          >
            {saving ? '저장 중...' : '다음'}
          </button>
        </div>

        <div className="progress-indicator">
          <span className="progress-dot active"></span>
          <span className="progress-dot"></span>
          <span className="progress-dot"></span>
        </div>
      </div>
    </div>
  );
}