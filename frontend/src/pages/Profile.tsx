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

export default function Profile() {
  const navigate = useNavigate();
  const [allergies, setAllergies] = useState<Allergy[]>([]);
  const [name, setName] = useState<string>('');
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
        if (user.name) {
          setName(user.name);
        }
        if (user.diet_type) {
          setSelectedDietType(user.diet_type);
        }
        if (user.allergies && user.allergies.length > 0) {
          setSelectedAllergies(user.allergies.map((a) => a.allergy_id));
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
    if (!name || name.trim().length === 0) {
      alert('이름을 입력해주세요.');
      return;
    }

    setSaving(true);
    try {
      const response = await userService.updateProfile({
        name: name.trim(),
        diet_type: selectedDietType,
        allergy_ids: selectedAllergies,
      });

      if (response.success) {
        alert('프로필이 성공적으로 업데이트되었습니다.');
        navigate('/');
      } else {
        alert('프로필 저장 실패: ' + response.message);
      }
    } catch (error) {
      console.error('Save error:', error);
      alert('프로필 저장 중 오류가 발생했습니다.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="profile-page">
        <div className="loading">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <div className="profile-container">
        <div className="profile-header">
          <h1>프로필 수정</h1>
          <p>이름, 식단 타입, 알레르기 정보를 수정할 수 있습니다.</p>
        </div>

        <div className="profile-section">
          <h2>이름</h2>
          <input
            type="text"
            className="name-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="이름을 입력하세요"
          />
        </div>

        <div className="profile-section">
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

        <div className="profile-section">
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

        <div className="profile-actions">
          <button
            onClick={handleSave}
            disabled={saving}
            className="btn-save"
          >
            {saving ? '저장 중...' : '저장하기'}
          </button>
          <button
            onClick={() => navigate('/')}
            className="btn-cancel"
          >
            취소
          </button>
        </div>
      </div>
    </div>
  );
}
