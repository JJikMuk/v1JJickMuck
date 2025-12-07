import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { allergyService } from '../services/allergy.service';
import type { Allergy } from '../services/allergy.service';
import { userService } from '../services/user.service';

const dietTypes = [
  { value: 'none', label: '없음' },
  { value: 'vegetarian', label: '채식주의 (Vegetarian)' },
  { value: 'vegan', label: '비건 (Vegan)' },
  { value: 'halal', label: '할랄 (Halal)' },
  { value: 'kosher', label: '코셔 (Kosher)' },
  { value: 'pescatarian', label: '페스카테리언 (Pescatarian)' },
];

export default function Settings() {
  const navigate = useNavigate();
  const [allergies, setAllergies] = useState<Allergy[]>([]);
  const [selectedAllergies, setSelectedAllergies] = useState<number[]>([]);
  const [selectedDietType, setSelectedDietType] = useState<string>('none');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // 알레르기 목록 가져오기
      const allergyResponse = await allergyService.getAllAllergies();
      if (allergyResponse.success && allergyResponse.data) {
        setAllergies(allergyResponse.data);
      }

      // 사용자 프로필 가져오기 (기존 설정값)
      const profileResponse = await userService.getProfile();
      if (profileResponse.success && profileResponse.data) {
        const user = profileResponse.data;
        if (user.diet_type) {
          setSelectedDietType(user.diet_type);
        }
        if (user.allergies && user.allergies.length > 0) {
          setSelectedAllergies(user.allergies.map((a: { allergy_id: number }) => a.allergy_id));
        }
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAllergyToggle = (allergyId: number) => {
    setSelectedAllergies((prev) =>
      prev.includes(allergyId)
        ? prev.filter((id) => id !== allergyId)
        : [...prev, allergyId]
    );
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await userService.updateProfile({
        diet_type: selectedDietType,
        allergy_ids: selectedAllergies,
      });

      if (response.success) {
        // 설정 완료 후 업로드 페이지로 이동
        navigate('/upload');
      } else {
        alert('설정 저장 실패: ' + response.message);
      }
    } catch (error) {
      console.error('Save error:', error);
      alert('설정 저장 중 오류가 발생했습니다.');
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
      <button
        className="back-edge-button"
        onClick={() => navigate('/health-conditions')}
        aria-label="이전 페이지로"
      >
        &lt;&lt;&lt;
      </button>
      <div className="settings-container">
        <div className="progress-bar-wrapper">
          <div className="progress-bar-track">
            <div className="progress-bar-fill" style={{ width: '100%' }}></div>
          </div>
          <div className="progress-steps">
            <span className="progress-step-label completed">신체 정보</span>
            <span className="progress-step-label completed">건강 상태</span>
            <span className="progress-step-label active">식단 설정</span>
          </div>
        </div>

        <div className="settings-header">
          <h1>알레르기 및 식단 설정</h1>
          <p>안전한 식사를 위해 알레르기와 식단 타입을 설정해주세요.</p>
        </div>

        <div className="settings-section">
          <h2>식단 타입</h2>
          <div className="diet-type-grid">
            {dietTypes.map((diet) => (
              <label key={diet.value} className="diet-type-option">
                <input
                  type="radio"
                  name="diet_type"
                  value={diet.value}
                  checked={selectedDietType === diet.value}
                  onChange={(e) => setSelectedDietType(e.target.value)}
                />
                <span>{diet.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="settings-section">
          <h2>알레르기 항목</h2>
          <p className="section-description">
            해당되는 알레르기 항목을 모두 선택해주세요.
          </p>
          <div className="allergy-grid">
            {allergies.map((allergy) => (
              <label key={allergy.id} className="allergy-option">
                <input
                  type="checkbox"
                  checked={selectedAllergies.includes(allergy.id)}
                  onChange={() => handleAllergyToggle(allergy.id)}
                />
                <span>{allergy.display_name}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="settings-actions">
          <button
            onClick={handleSave}
            disabled={saving}
            className="btn-save"
          >
            {saving ? '저장 중...' : '저장하고 계속하기'}
          </button>
        </div>

        <div className="progress-indicator">
          <span className="progress-dot"></span>
          <span className="progress-dot"></span>
          <span className="progress-dot active"></span>
        </div>
      </div>
    </div>
  );
}