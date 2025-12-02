from ultralytics import YOLO # yolo 모델을 사용한 객체 탐지를 하기 위한 import
import easyocr # easyocr 모델을 사용한 텍스트 추출을 하기 위한 import

from typing import List
import cv2
import numpy as np
import matplotlib.pyplot as plt

import re # 정규식을 사용하기 위한 import
from difflib import SequenceMatcher # 문자열의 유사도 비교를 위한 import

class MaterialImageToText:
    def __init__(self, VISUALIZATION=False):
        self.__visualization = VISUALIZATION
        self.__allergen_list = ['밀', '우유', '대두', '돼지고기', '쇠고기', '아황산류', '계란', '땅콩']

        self.__yolo = None
        self.__easy_ocr = None

    def __yolo_execute(self, image: np.ndarray, toleranceY: int = 10) -> List[np.ndarray]:
        """
        YOLO를 사용하여 이미지에서 객체를 감지하고, 감지된 영역을 crop하여 리스트로 반환
        
        Parameters:
            image (str): 이미지 파일 경로
            visualization_mode (bool): True이면 crop된 이미지들을 시각화
            toleranceY (int): y좌표 정렬 시 허용 오차 범위
        
        Returns:
            List[np.ndarray]: crop된 이미지 리스트
        """
        # 1)
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 2) YOLO 실행
        results = self.__yolo(img_rgb)[0]
        boxes = results.boxes.xyxy.cpu().numpy()  # (N,4) numpy array: x1,y1,x2,y2

        # 3) 좌표 정렬 (y좌표 우선, x좌표 다음)
        def sort_key(box):
            x1, y1, x2, y2 = box
            # toleranceY를 고려하여 그룹화
            return (int(y1 / toleranceY), x1)
        
        boxes_sorted = sorted(boxes, key=sort_key)

        # 4) crop
        cropped_list = []
        for box in boxes_sorted:
            x1, y1, x2, y2 = map(int, box)
            crop_img = img_rgb[y1:y2, x1:x2]
            cropped_list.append(crop_img)

        # 5) visualization
        if self.__visualization and cropped_list:
        # 모든 crop 이미지를 10x10으로 resize
            resized_crops = [cv2.resize(c, (200, 50)) for c in cropped_list]
            
            # matplotlib으로 20개씩 줄바꿈하여 시각화
            num_per_row = 5
            num_rows = (len(resized_crops) + num_per_row - 1) // num_per_row
            plt.figure(figsize=(num_per_row, num_rows))
            
            for i, c in enumerate(resized_crops):
                plt.subplot(num_rows, num_per_row, i + 1)
                plt.imshow(c)
                plt.axis('off')
            
            plt.tight_layout()
            plt.show()


        return cropped_list

        # easyocr execute

    def __easyocr_execute(self, images: list[np.ndarray]) -> list[str]:
        """
        EasyOCR 모델을 사용하여 여러 이미지에서 텍스트를 추출합니다.
        
        Args:
            images (list): 이미지 객체들이 들어있는 리스트(OpenCV 이미지, PIL 이미지 등)
        
        Returns:
            list[str]: 각 이미지에서 추출한 텍스트 리스트
        """
        results = []
        
        for img in images:
            # easy_ocr 모델을 사용하여 텍스트 추출
            ocr_result = self.__easy_ocr.readtext(img, detail=0)  # detail=0 -> 텍스트만 반환
            # 추출된 텍스트를 하나의 문자열로 합치거나 리스트 그대로 추가 가능
            results.append(" ".join(ocr_result))  # 여러 줄이면 공백으로 연결
        
        return results

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

        return SequenceMatcher(None, decomposed_a, decomposed_b).ratio()
    
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

    class str_or_ndarray: # 타입 힌트용
        pass

    def execute(self, image:str_or_ndarray) -> list[str]:
        result = []
        
        # 이미지의 경로를 cv2로 읽어들여 numpy로 변환함
        img = image
        
        if(type(img) == str):
            img = cv2.imread(img)
        
        yolo_result = self.__yolo_execute(img)
        easyocr_result = self.__easyocr_execute(yolo_result)
        
        for r in easyocr_result:
            for allergen in self.__allergen_list:
                similar_ratio = self.__similar(r, allergen)

                if(similar_ratio > 0.8):
                    result += [allergen]

        return result