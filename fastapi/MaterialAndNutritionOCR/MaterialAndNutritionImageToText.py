import cv2

from MaterialAndNutritionOCR.MaterialImageToText import MaterialImageToText
from MaterialAndNutritionOCR.NutritionImageToText import NutritionImageToText
import easyocr

class MaterialAndNutritionImageToText:
    def __init__(self):
        self.__niit = NutritionImageToText()
        self.__miit = MaterialImageToText()
        self.__easy_ocr = None

    def load_nutrition_yolo(self):
        self.__niit.load_yolo("MaterialAndNutritionOCR/nutrition_yolo.pt")

    def load_material_yolo(self):
        self.__miit.load_yolo("MaterialAndNutritionOCR/material_yolo.pt")

    def load_easyocr(self):
        # 2️⃣ EasyOCR 불러오기
        self.__easy_ocr = easyocr.Reader(['ko', 'en'])

        self.__niit.set_easyocr(self.__easy_ocr)
        self.__miit.set_easyocr(self.__easy_ocr)
        
    class str_or_ndarray:
        pass

    def execute(self, image:str_or_ndarray):
        # 이미지의 경로를 cv2로 읽어들여 numpy로 변환함
        img = image
        
        if(type(img) == str):
            img = cv2.imread(img)

        nutrition_result, _ = self.__niit.execute(img)
        material_result = self.__miit.execute(img)

        return nutrition_result, material_result