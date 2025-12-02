"""
OCR 테스트 스크립트
테스트 이미지로 FastAPI의 OCR 기능을 테스트합니다.
"""
import requests
import json
import os

# FastAPI URL
FASTAPI_URL = "http://localhost:8000"

def test_health():
    """헬스 체크 테스트"""
    response = requests.get(f"{FASTAPI_URL}/health")
    print("=== 헬스 체크 ===")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.status_code == 200

def test_ocr_with_sample():
    """샘플 이미지로 OCR 테스트"""
    # 테스트용 사용자 정보
    user_info = {
        "user_id": "test_user",
        "diet_type": "none",
        "allergies": ["우유", "땅콩"],
        "height": 175,
        "weight": 70,
        "age_range": "20대",
        "gender": "male",
        "diseases": [],
        "special_conditions": []
    }
    
    # 테스트 이미지 경로 (있으면 사용, 없으면 더미 데이터)
    test_images = [
        "test_image.jpg",
        "test_image.png",
        "sample.jpg",
        "sample.png"
    ]
    
    image_path = None
    for img in test_images:
        if os.path.exists(img):
            image_path = img
            break
    
    if not image_path:
        print("\n⚠️ 테스트 이미지가 없습니다.")
        print("다음 중 하나의 이미지 파일을 fastapi 폴더에 추가해주세요:")
        print("  - test_image.jpg")
        print("  - test_image.png")
        print("  - sample.jpg")
        print("  - sample.png")
        print("\n또는 curl 명령어로 직접 테스트:")
        print('curl -X POST "http://localhost:8000/api/upload" \\')
        print('  -F "file=@your_image.jpg" \\')
        print('  -F \'user_info={"user_id":"test","diet_type":"none","allergies":["우유"]}\'')
        return
    
    print(f"\n=== OCR 테스트 (이미지: {image_path}) ===")
    
    with open(image_path, 'rb') as f:
        files = {'file': (image_path, f, 'image/jpeg')}
        data = {'user_info': json.dumps(user_info)}
        
        response = requests.post(
            f"{FASTAPI_URL}/api/upload",
            files=files,
            data=data
        )
    
    print(f"상태 코드: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print("🧪 FastAPI OCR 테스트 시작\n")
    
    if test_health():
        print("\n✅ 서버 정상 작동")
        test_ocr_with_sample()
    else:
        print("\n❌ 서버 연결 실패")
