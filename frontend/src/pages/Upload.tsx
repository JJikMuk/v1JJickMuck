import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { imageService } from '../services/image.service';
import type { AnalysisResult } from '../types';

export default function Upload() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // 이미지 파일인지 확인
      if (!file.type.startsWith('image/')) {
        alert('이미지 파일만 업로드 가능합니다.');
        return;
      }

      setSelectedFile(file);

      // 미리보기 URL 생성
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string);
      };
      reader.readAsDataURL(file);

      // 이전 결과 초기화
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      alert('먼저 이미지를 선택해주세요.');
      return;
    }

    setUploading(true);
    try {
      const response = await imageService.uploadImage(selectedFile);

      if (response.success && response.data?.fastapi_response) {
        setResult(response.data.fastapi_response);
      } else {
        alert('업로드 실패: ' + response.message);
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('이미지 업로드 중 오류가 발생했습니다.');
    } finally {
      setUploading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'red':
        return '#ff4444';
      case 'yellow':
        return '#ffbb33';
      case 'green':
        return '#00C851';
      default:
        return '#999';
    }
  };

  const getRiskEmoji = (level: string) => {
    switch (level) {
      case 'red':
        return '🔴';
      case 'yellow':
        return '🟡';
      case 'green':
        return '🟢';
      default:
        return '⚪';
    }
  };

  const getRiskText = (level: string) => {
    switch (level) {
      case 'red':
        return '위험';
      case 'yellow':
        return '주의';
      case 'green':
        return '안전';
      default:
        return '알 수 없음';
    }
  };

  return (
    <div className="upload-page">
      <div className="upload-container">
        <div className="upload-header">
          <button onClick={() => navigate('/')} className="btn-back">
            ← 홈으로
          </button>
          <h1>음식 사진 분석</h1>
          <p>음식 사진을 업로드하면 AI가 알레르기 정보를 분석합니다.</p>
        </div>

        <div className="upload-content">
          {!previewUrl ? (
            <div className="upload-area">
              <input
                type="file"
                id="file-input"
                accept="image/*"
                onChange={handleFileSelect}
                className="file-input"
              />
              <label htmlFor="file-input" className="upload-label">
                <div className="upload-icon">📷</div>
                <p className="upload-text">클릭하여 이미지 선택</p>
                <p className="upload-hint">또는 이미지를 드래그 앤 드롭</p>
              </label>
            </div>
          ) : (
            <div className="preview-section">
              <div className="image-preview">
                <img src={previewUrl} alt="Preview" />
              </div>

              <div className="upload-actions">
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="btn-upload"
                >
                  {uploading ? '분석 중...' : '분석 시작'}
                </button>
                <button
                  onClick={handleReset}
                  disabled={uploading}
                  className="btn-reset"
                >
                  다시 선택
                </button>
              </div>
            </div>
          )}

          {result && (
            <div className="result-section">
              <div className="traffic-light-container">
                <div
                  className="traffic-light"
                  style={{ borderColor: getRiskColor(result.risk_level) }}
                >
                  <div className="risk-icon">{getRiskEmoji(result.risk_level)}</div>
                  <div className="risk-label" style={{ color: getRiskColor(result.risk_level) }}>
                    {getRiskText(result.risk_level)}
                  </div>
                  <div className="risk-score">위험도: {result.risk_score ?? 0}%</div>
                </div>
              </div>

              <div className="recommendation-box">
                <h3>권장사항</h3>
                <p>{result.recommendation || '분석 결과를 확인해주세요.'}</p>
              </div>

              {result.analysis?.detected_ingredients?.length > 0 && (
                <div className="analysis-box">
                  <h3>검출된 성분</h3>
                  <div className="ingredient-list">
                    {result.analysis.detected_ingredients.map((ingredient, idx) => (
                      <span key={idx} className="ingredient-tag">
                        {ingredient}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {result.analysis?.allergen_warnings?.length > 0 && (
                <div className="warning-box allergen">
                  <h3>⚠️ 알레르기 경고</h3>
                  {result.analysis.allergen_warnings.map((warning, idx) => (
                    <div key={idx} className="warning-item">
                      <strong>{warning.allergen}</strong>
                      <span className={`severity severity-${warning.severity}`}>
                        {warning.severity === 'high' ? '높음' : warning.severity === 'medium' ? '중간' : '낮음'}
                      </span>
                      <p>{warning.message}</p>
                    </div>
                  ))}
                </div>
              )}

              {result.analysis?.diet_warnings?.length > 0 && (
                <div className="warning-box diet">
                  <h3>🍽️ 식단 주의사항</h3>
                  {result.analysis.diet_warnings.map((warning, idx) => (
                    <div key={idx} className="warning-item">
                      <strong>{warning.ingredient}</strong>
                      <p>{warning.reason}</p>
                    </div>
                  ))}
                </div>
              )}

              {result.ocr_text && (
                <details className="ocr-details">
                  <summary>OCR 원문 보기</summary>
                  <pre className="ocr-text">{result.ocr_text}</pre>
                </details>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
