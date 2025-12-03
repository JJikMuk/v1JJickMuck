import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { userService } from '../services/user.service';
import '../styles/settings.css';

interface Disease {
  id: number;
  name: string;
  display_name: string;
}

interface SpecialCondition {
  id: number;
  name: string;
  display_name: string;
}

export default function HealthConditionsSettings() {
  const navigate = useNavigate();
  const [diseases, setDiseases] = useState<Disease[]>([]);
  const [conditions, setConditions] = useState<SpecialCondition[]>([]);
  const [selectedDiseaseIds, setSelectedDiseaseIds] = useState<number[]>([]);
  const [selectedConditionIds, setSelectedConditionIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      // 마스터 데이터 로드
      const [diseasesRes, conditionsRes, profileRes] = await Promise.all([
        userService.getAllDiseases(),
        userService.getAllSpecialConditions(),
        userService.getFullProfile(),
      ]);

      if (diseasesRes.success && diseasesRes.data) {
        setDiseases(diseasesRes.data);
      }

      if (conditionsRes.success && conditionsRes.data) {
        setConditions(conditionsRes.data);
      }

      // 기존 선택값 로드
      if (profileRes.success && profileRes.data) {
        const user = profileRes.data;
        
        // 질병 ID 매칭
        if (user.diseases && diseasesRes.data) {
          const diseaseIds = diseasesRes.data
            .filter((d: Disease) => user.diseases.includes(d.display_name))
            .map((d: Disease) => d.id);
          setSelectedDiseaseIds(diseaseIds);
        }

        // 특수 상태 ID 매칭
        if (user.special_conditions && conditionsRes.data) {
          const conditionIds = conditionsRes.data
            .filter((c: SpecialCondition) => user.special_conditions.includes(c.display_name))
            .map((c: SpecialCondition) => c.id);
          setSelectedConditionIds(conditionIds);
        }
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleDisease = (id: number) => {
    setSelectedDiseaseIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const toggleCondition = (id: number) => {
    setSelectedConditionIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleNext = async () => {
    setSaving(true);
    try {
      // 질병 업데이트
      const diseaseRes = await userService.updateDiseases(selectedDiseaseIds);
      if (!diseaseRes.success) {
        alert('질병 저장 실패: ' + diseaseRes.message);
        return;
      }

      // 특수 상태 업데이트
      const conditionRes = await userService.updateSpecialConditions(selectedConditionIds);
      if (!conditionRes.success) {
        alert('특수 상태 저장 실패: ' + conditionRes.message);
        return;
      }

      // 다음 페이지 (알레르기/식단 설정)로 이동
      navigate('/settings');
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
          <h1>건강 상태 설정</h1>
          <p>해당되는 질병이나 특수 상태를 선택해주세요.</p>
        </div>

        <div className="settings-section">
          <h2>질병/건강 상태</h2>
          <p className="section-description">
            현재 앓고 있는 질병이 있다면 선택해주세요.
          </p>
          <div className="condition-grid">
            {diseases.map((disease) => (
              <label key={disease.id} className="condition-option disease">
                <input
                  type="checkbox"
                  checked={selectedDiseaseIds.includes(disease.id)}
                  onChange={() => toggleDisease(disease.id)}
                />
                <span>{disease.display_name}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="settings-section">
          <h2>특수 상태</h2>
          <p className="section-description">
            해당되는 특수 상태가 있다면 선택해주세요.
          </p>
          <div className="condition-grid">
            {conditions.map((condition) => (
              <label key={condition.id} className="condition-option special">
                <input
                  type="checkbox"
                  checked={selectedConditionIds.includes(condition.id)}
                  onChange={() => toggleCondition(condition.id)}
                />
                <span>{condition.display_name}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="settings-actions">
          <button
            onClick={() => navigate('/health-settings')}
            className="btn-back"
          >
            이전
          </button>
          <button
            onClick={handleNext}
            disabled={saving}
            className="btn-save"
          >
            {saving ? '저장 중...' : '다음'}
          </button>
        </div>

        <div className="progress-indicator">
          <span className="progress-dot"></span>
          <span className="progress-dot active"></span>
          <span className="progress-dot"></span>
        </div>
      </div>
    </div>
  );
}