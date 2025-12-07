import React, { useState, useEffect } from 'react';
import {
  getAllAllergies,
  getAllDiseases,
  getAllSpecialConditions,
  getUserFullProfile,
  updateUserProfile,
  updateUserHealthProfile,
  updateUserDiseases,
  updateUserSpecialConditions,
} from '../services/api';
import '../styles/profile.css';

interface MasterData {
  id: number;
  name: string;
  display_name: string;
}

const Profile: React.FC = () => {
  // 로딩 상태
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // 마스터 데이터
  const [allergies, setAllergies] = useState<MasterData[]>([]);
  const [diseases, setDiseases] = useState<MasterData[]>([]);
  const [conditions, setConditions] = useState<MasterData[]>([]);

  // 유저 프로필
  const [name, setName] = useState('');
  const [dietType, setDietType] = useState('');
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [ageRange, setAgeRange] = useState('');
  const [gender, setGender] = useState('');
  const [selectedAllergyIds, setSelectedAllergyIds] = useState<number[]>([]);
  const [selectedDiseaseIds, setSelectedDiseaseIds] = useState<number[]>([]);
  const [selectedConditionIds, setSelectedConditionIds] = useState<number[]>([]);

  // 옵션 데이터
  const ageRanges = ['10대', '20대', '30대', '40대', '50대', '60대 이상'];
  const genders = [
    { value: 'male', label: '남성' },
    { value: 'female', label: '여성' },
    { value: 'other', label: '기타' },
  ];
  const dietTypes = [
    { value: 'normal', label: '일반' },
    { value: 'vegetarian', label: '채식주의' },
    { value: 'vegan', label: '비건' },
    { value: 'pescatarian', label: '페스코' },
    { value: 'halal', label: '할랄' },
    { value: 'kosher', label: '코셔' },
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);

      // 마스터 데이터 로드
      const [allergiesData, diseasesData, conditionsData, profileData] = await Promise.all([
        getAllAllergies(),
        getAllDiseases(),
        getAllSpecialConditions(),
        getUserFullProfile(),
      ]);

      setAllergies(allergiesData);
      setDiseases(diseasesData);
      setConditions(conditionsData);

      // 프로필 데이터 설정
      setName(profileData.name || '');
      setDietType(profileData.diet_type || '');
      setHeight(profileData.height?.toString() || '');
      setWeight(profileData.weight?.toString() || '');
      setAgeRange(profileData.age_range || '');
      setGender(profileData.gender || '');

      // ID 매칭 (display_name으로 비교)
      setSelectedAllergyIds(
        allergiesData
          .filter((a: MasterData) => profileData.allergies.includes(a.display_name))
          .map((a: MasterData) => a.id)
      );
      setSelectedDiseaseIds(
        diseasesData
          .filter((d: MasterData) => profileData.diseases.includes(d.display_name))
          .map((d: MasterData) => d.id)
      );
      setSelectedConditionIds(
        conditionsData
          .filter((c: MasterData) => profileData.special_conditions.includes(c.display_name))
          .map((c: MasterData) => c.id)
      );
    } catch (error) {
      console.error('Failed to load data:', error);
      alert('데이터를 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);

      // 기본 프로필 업데이트
      await updateUserProfile({
        name,
        diet_type: dietType || null,
        allergy_ids: selectedAllergyIds,
      });

      // 건강 프로필 업데이트
      await updateUserHealthProfile({
        height: height ? parseFloat(height) : undefined,
        weight: weight ? parseFloat(weight) : undefined,
        age_range: ageRange || undefined,
        gender: gender || undefined,
      });

      // 질병 업데이트
      await updateUserDiseases(selectedDiseaseIds);

      // 특수 상태 업데이트
      await updateUserSpecialConditions(selectedConditionIds);

      alert('프로필이 저장되었습니다.');
    } catch (error) {
      console.error('Failed to save profile:', error);
      alert('저장에 실패했습니다.');
    } finally {
      setIsSaving(false);
    }
  };

  const toggleSelection = (
    id: number,
    selectedIds: number[],
    setSelectedIds: React.Dispatch<React.SetStateAction<number[]>>
  ) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((i) => i !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  if (isLoading) {
    return <div className="loading">로딩 중...</div>;
  }

  return (
    <div className="profile-settings-page">
      <h1>프로필 설정</h1>

      {/* 기본 정보 */}
      <section className="section">
        <h2>기본 정보</h2>
        <div className="form-group">
          <label>이름</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="이름을 입력하세요"
          />
        </div>
        <div className="form-group">
          <label>식단 타입</label>
          <select value={dietType} onChange={(e) => setDietType(e.target.value)}>
            <option value="">선택하세요</option>
            {dietTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </section>

      {/* 신체 정보 */}
      <section className="section">
        <h2>신체 정보</h2>
        <div className="form-row">
          <div className="form-group">
            <label>키 (cm)</label>
            <input
              type="number"
              value={height}
              onChange={(e) => setHeight(e.target.value)}
              placeholder="170"
            />
          </div>
          <div className="form-group">
            <label>몸무게 (kg)</label>
            <input
              type="number"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              placeholder="65"
            />
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>연령대</label>
            <select value={ageRange} onChange={(e) => setAgeRange(e.target.value)}>
              <option value="">선택하세요</option>
              {ageRanges.map((age) => (
                <option key={age} value={age}>
                  {age}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>성별</label>
            <select value={gender} onChange={(e) => setGender(e.target.value)}>
              <option value="">선택하세요</option>
              {genders.map((g) => (
                <option key={g.value} value={g.value}>
                  {g.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      {/* 알레르기 */}
      <section className="section">
        <h2>알레르기</h2>
        <div className="chip-container">
          {allergies.map((allergy) => (
            <button
              key={allergy.id}
              className={`chip ${selectedAllergyIds.includes(allergy.id) ? 'selected' : ''}`}
              onClick={() => toggleSelection(allergy.id, selectedAllergyIds, setSelectedAllergyIds)}
            >
              {allergy.display_name}
            </button>
          ))}
        </div>
      </section>

      {/* 질병/건강 상태 */}
      <section className="section">
        <h2>질병/건강 상태</h2>
        <div className="chip-container">
          {diseases.map((disease) => (
            <button
              key={disease.id}
              className={`chip disease ${selectedDiseaseIds.includes(disease.id) ? 'selected' : ''}`}
              onClick={() => toggleSelection(disease.id, selectedDiseaseIds, setSelectedDiseaseIds)}
            >
              {disease.display_name}
            </button>
          ))}
        </div>
      </section>

      {/* 특수 상태 */}
      <section className="section">
        <h2>특수 상태</h2>
        <div className="chip-container">
          {conditions.map((condition) => (
            <button
              key={condition.id}
              className={`chip condition ${selectedConditionIds.includes(condition.id) ? 'selected' : ''}`}
              onClick={() => toggleSelection(condition.id, selectedConditionIds, setSelectedConditionIds)}
            >
              {condition.display_name}
            </button>
          ))}
        </div>
      </section>

      {/* 저장 버튼 */}
      <button className="save-button" onClick={handleSave} disabled={isSaving}>
        {isSaving ? '저장 중...' : '저장하기'}
      </button>
    </div>
  );
};

export default Profile;
