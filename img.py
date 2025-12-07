import os
import glob
import random
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from pillow_heif import register_heif_opener
register_heif_opener()

input_dir = "opic"    
output_dir = "tpic"     
target_per_image = 30         
output_size = (512, 512)     

os.makedirs(output_dir, exist_ok=True)

def augment_image(img: Image.Image) -> Image.Image:
    # 1) 기본 리사이즈
    img = img.resize(output_size)

    # 2) 작은 각도 회전 (텍스트가 안 망가지게 ±5도 정도)
    angle = random.uniform(-5, 5)
    img = img.rotate(angle, expand=True, fillcolor=(255, 255, 255))
    # 회전으로 크기가 바뀌었으니 다시 512x512로 맞춰줌
    img = ImageOps.fit(img, output_size, method=Image.BICUBIC)

    # 3) 밝기/대비/색감 약간 조정
    if random.random() < 0.9:
        b_factor = random.uniform(0.8, 1.2)   # 밝기
        c_factor = random.uniform(0.8, 1.2)   # 대비
        s_factor = random.uniform(0.9, 1.1)   # 채도(색감)

        img = ImageEnhance.Brightness(img).enhance(b_factor)
        img = ImageEnhance.Contrast(img).enhance(c_factor)
        img = ImageEnhance.Color(img).enhance(s_factor)

    # 4) 약간의 블러(가끔만)
    if random.random() < 0.3:
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0, 0.8)))

    return img

extensions = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.heic", "*.HEIC"]


image_paths = []
for ext in extensions:
    image_paths.extend(glob.glob(os.path.join(input_dir, ext)))

print(f"발견한 원본 이미지 개수: {len(image_paths)}")

if len(image_paths) == 0:
    raise ValueError("input_dir에 이미지가 없습니다. input_dir 경로와 이미지 확장자를 확인하세요.")

for idx, img_path in enumerate(image_paths):
    img_name = os.path.splitext(os.path.basename(img_path))[0]
    img = Image.open(img_path).convert("RGB")

    img_resized = img.resize(output_size)
    save_path_orig = os.path.join(output_dir, f"{img_name}_orig.jpg")
    img_resized.save(save_path_orig, quality=95)

    num_aug = target_per_image - 1 
    for i in range(num_aug):
        aug_img = augment_image(img)
        save_path_aug = os.path.join(output_dir, f"{img_name}_aug_{i+1}.jpg")
        aug_img.save(save_path_aug, quality=95)

    print(f"[{idx+1}/{len(image_paths)}] {img_name} → 총 {target_per_image}장 생성 완료")

print("끝")