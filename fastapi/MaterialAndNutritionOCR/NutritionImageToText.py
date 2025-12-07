from ultralytics import YOLO # yolo 모델을 사용한 객체 탐지를 하기 위한 import
import easyocr # easyocr 모델을 사용한 텍스트 추출을 하기 위한 import

import re # 정규식을 사용하기 위한 import
import numpy as np # 이미지를 넘파이 배열로 변환을 하기 위한 import
from difflib import SequenceMatcher # 문자열의 유사도 비교를 위한 import

import cv2 # OCR클래스의 DEV_MODE가 True일때의 시각화를 위한 import
import matplotlib.pyplot as plt # OCR클래스의 DEV_MODE가 True일때의 시각화를 위한 import

class NutritionImageToText:
    def __init__(self, VISUALIZATION = False):
        self.__yolo = None
        self.__easy_ocr = None

        self.__visualization = VISUALIZATION
        self.__match_ratio_deadline = 0.7 # 패턴 매칭시 유사도가 이 수치 보다 낮은 녀석의 경우 버림

    def load_yolo(self, yolo_model_path:str):
        # 1️⃣ YOLO 모델 불러오기
        self.__yolo = YOLO(yolo_model_path)
    def set_yolo(self, yolo_model):
        self.__yolo = yolo_model

    def load_easyocr(self):
        # 2️⃣ EasyOCR 불러오기
        self.__easy_ocr = easyocr.Reader(['ko', 'en'])
    def set_easyocr(self, easy_ocr):
            self.__easy_ocr = easy_ocr
            
    def __decompose_hangul(self, s: str) -> str:
        """
        문자열 내 한글을 초성/중성/종성 단위로 분해하여 반환.
        예: "열량" -> "ㅇㅕㄹㄹㅑㅇ"
        """
        CHO = ["ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ","ㅆ","ㅇ",
            "ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]
        JUNG = ["ㅏ","ㅐ","ㅑ","ㅒ","ㅓ","ㅔ","ㅕ","ㅖ","ㅗ","ㅘ","ㅙ","ㅚ",
                "ㅛ","ㅜ","ㅝ","ㅞ","ㅟ","ㅠ","ㅡ","ㅢ","ㅣ"]
        JONG = ["","ㄱ","ㄲ","ㄳ","ㄴ","ㄵ","ㄶ","ㄷ","ㄹ","ㄺ","ㄻ","ㄼ","ㄽ","ㄾ","ㄿ",
                "ㅀ","ㅁ","ㅂ","ㅄ","ㅅ","ㅆ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]

        result = []

        for ch in s:
            code = ord(ch)

            # 한글 범위 (가~힣)
            if 0xAC00 <= code <= 0xD7A3:
                base = code - 0xAC00
                cho = base // 588
                jung = (base % 588) // 28
                jong = base % 28

                result.append(CHO[cho])
                result.append(JUNG[jung])
                if JONG[jong] != "":
                    result.append(JONG[jong])

            else:
                # 한글이 아니면 그대로 추가
                result.append(ch)

        return "".join(result)

    def __similar(self, a: str, b: str) -> float:
        """두 문자열의 유사도 계산 (0~1)"""

        cleaned_a = re.sub(r"[0-9A-Za-z]", "", a)
        cleaned_b = re.sub(r"[0-9A-Za-z]", "", b)

        decomposed_a = self.__decompose_hangul(cleaned_a)
        decomposed_b = self.__decompose_hangul(cleaned_b)

        if(self.__visualization):
            print(f"패턴 매칭 유사도 결과 -  \"{a}\"와 같은 텍스트 내용이, \"{b}\"에 대한 내용인지에 대한 유사도 = {SequenceMatcher(None, decomposed_a, decomposed_b).ratio()}") # DEV
        
        return SequenceMatcher(None, decomposed_a, decomposed_b).ratio()

    def __extract_first_number(self, text: str):
        """문자열에서 첫 번째 숫자를 추출"""
        # 알파벳 O → 0 변환
        text = text.replace("O", "0").replace("o", "0")
        match = re.search(r"\d+\.?\d*", text)
        if match:
            return float(match.group())
        return None

    def __image_to_text(self, image: np.ndarray, yolo, easy_ocr) -> dict[str, list]:
        # ------------------------------------------
        # 1) YOLO로 detection 수행
        # ------------------------------------------
        results = yolo(image)[0]     # result 객체 하나
        boxes = results.boxes.xyxy   # tensor: (N, 4)

        cropped_list = []

        # ------------------------------------------
        # 2) bounding box 기반 crop 이미지 생성
        # ------------------------------------------
        for box in boxes:
            x1, y1, x2, y2 = box.int().tolist()
            crop = image[y1:y2, x1:x2]
            cropped_list.append(crop)

        ##### OCR전 실제로 크롭된 이미지를 확인하기 위한 코드
        if(self.__visualization):
            if len(cropped_list) == 0:
                print("⚠️ YOLO 감지 결과 없음(cropped_list가 비어 있습니다)")
            else:
                print(f"yolo가 검출한 좌표를 토대로 crop한, 총 {len(cropped_list)}개의 이미지를 시각화 합니다")

                # 한 줄에 4개씩 배치 (원하면 수정 가능)
                cols = 4
                rows = (len(cropped_list) + cols - 1) // cols

                plt.figure(figsize=(12, 3 * rows))

                for i, crop in enumerate(cropped_list):
                    plt.subplot(rows, cols, i + 1)
                    # OpenCV는 BGR, matplotlib은 RGB → 변환
                    crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                    plt.imshow(crop_rgb)
                    plt.axis("off")
                    plt.title(f"crop {i}")

                plt.tight_layout()
                plt.show()

        # ------------------------------------------
        # 3) EasyOCR로 모든 crop 이미지에서 텍스트 추출
        #    형태: [ [text, confidence], ... ]
        # ------------------------------------------
        original_ocr_result = []

        for crop in cropped_list:
            ocr_result = easy_ocr.readtext(crop)

            # 현재 crop에서 읽힌 모든 text를 하나로 합침
            texts = []
            confs = []

            for (_, text, conf) in ocr_result:
                text = text.strip()
                if text == "":
                    continue
                texts.append(text)
                confs.append(float(conf))

            # 아무 글자도 없다면 패스
            if len(texts) == 0:
                continue

            # crop 하나당 하나의 문자열로 합침
            merged_text = " ".join(texts)

            # 신뢰도는 평균 또는 최대값 사용 (원하는 방식 선택)
            avg_conf = sum(confs) / len(confs)

            # 이제 하나만 저장
            original_ocr_result.append([merged_text, avg_conf])

        ##### 패턴 매칭전 문자열을 확인하기 위한 코드
        if(self.__visualization):
            print("패턴 매칭전 결과(easyocr의 순수 결과값) : ", original_ocr_result)

        # ------------------------------------------
        # 4) 패턴 정의
        # ------------------------------------------
        patterns = {
            "총내용량": ["총내용량"],
            # "기준내용량"은 따로 정규식을 사용하여 처리 ex) "100ml당", "50g당"
            # "kcal"는 따로 정규식을 사용하여 처리 ex) "300kcal", "600kcal"
            "나트륨": ["나트륨", "나르룹"],
            "탄수화물": ["탄수화물"],
            "당류": ["당류"],
            "지방": ["지방"],
            "트랜스지방": ["트랜스지방"],
            "포화지방": ["포화지방"],
            "콜레스테롤": ["콜레스테롤"],
            "단백질": ["단백질"]
        }

        matched = {key: None for key in patterns.keys()}

        # ------------------------------------------
        # 5) 문자열 패턴 매칭
        # ------------------------------------------
        for ocr_original_text, ocr_conf in original_ocr_result:
            ocr_text = ocr_original_text.replace(" ", "").replace("(", "").replace(")", "")

            # ✔ 패턴1: 수치 + kcal
            if re.search(r"\d+\.?\d*\s*kcal", ocr_text.lower()):
                matched["kcal"] = [ocr_text, ocr_conf, 1] # 매칭이 되었을 경우 패턴 매칭 유사도를 1로 취급
                continue

            # ✔ 패턴2: 수치 + 단위 + "당"
            is_standard_amount = True

            if("류" in ocr_text.lower()):
                is_standard_amount = False

            if("kc" in ocr_text.lower() or "cal" in ocr_text.lower()):
                is_standard_amount = False

            if("당" not in ocr_text.lower()):
                is_standard_amount = False

            if(is_standard_amount):
                matched["기준내용량"] = [ocr_text, ocr_conf, 1] # 매칭이 되었을 경우 패턴 매칭 유사도를 1로 취급
                continue

            # ✔ 패턴3: "총내용량", "나트륨" 등 유사도 기반
            if(self.__visualization):
                print(f"===== easyocr이 변환한 \"{ocr_text}\"에 대한 패턴 매칭 시작 =====")

            for category, keywords in patterns.items():
                for kw in keywords:
                    match_sim = self.__similar(ocr_text, kw)

                    if match_sim > self.__match_ratio_deadline:
                        # 이전 값이 없으면 바로 저장
                        if matched[category] is None:
                            matched[category] = [ocr_text, ocr_conf, match_sim] # conf = confidence(easyocr이 ocr한 텍스트에 대한 신뢰도)
                                                                                # sim = similar(영양소 종류 패턴 매칭에 대한 유사도)
                            break

                        # 이전에 저장된 유사도
                        old_sim = matched[category][2]

                        # 유사도가 기존보다 높을 때만 업데이트
                        if match_sim > old_sim:
                            matched[category] = [ocr_text, ocr_conf, match_sim]

                        break

        ##### easyocr이 추출한 문자열을 패턴 매칭한 이후의 결과를 확인하기 위한 코드 
        if(self.__visualization):
            print("패턴 매칭후 결과 : ", matched) # DEV

        # ------------------------------------------
        # 6) 매칭된 문자열에서 숫자 파싱
        # ------------------------------------------
        final_output = {}

        for key, val in matched.items():
            if val is None:
                continue

            ocr_text, ocr_conf, match_sim = val
            number = self.__extract_first_number(ocr_text)

            ##### 각 영양 정보별 파싱된 숫자들
            if(self.__visualization):
                print(f"{ocr_text}에 대한 파싱된 수치 : {number}") # DEV

            if number is not None:
                final_output[key] = [number, ocr_conf, match_sim]

        return final_output, original_ocr_result

    class str_or_ndarray: # 타입 힌트용
        pass

    # image는 경로(str) 또는 numpy 배열(np.ndarray)둘중 하나를 전달
    def execute(self, image:str_or_ndarray):
        # 이미지의 경로를 cv2로 읽어들여 numpy로 변환함
        img = image
        
        if(type(img) == str):
            img = cv2.imread(img)

        nutrition_result, original_ocr_result = self.__image_to_text(img, self.__yolo, self.__easy_ocr)

        try:
            if(nutrition_result["총내용량"][0] < 5): # 단위 변환 (L -> ml)
                nutrition_result["총내용량"][0] *= 1000
        except:
            pass

        return nutrition_result, original_ocr_result

if(__name__ == "__main__"):
    nitt = NutritionImageToText(False)

    nitt.load_yolo("Model/YOLO_nutrition_detection200/weights/best.pt")
    nitt.load_easyocr()

    image_num = 4

    nutrition_result, original_ocr_result = nitt.execute(f"DataSet/images/train/{image_num}.png") # 사용할 이미지 선택

    print(nutrition_result)