from PIL import Image, ImageDraw
import io
import json
import requests

def resize_image_width(image_file, target_width):
    # 이미지 열기
    with Image.open(image_file) as img:
        # 원본 크기
        original_size = img.size

        # 비율 유지하면서 새로운 세로 크기 계산
        aspect_ratio = original_size[1] / original_size[0]  # 세로:가로 비율
        new_size = (target_width, int(target_width * aspect_ratio))  # 새로운 크기 계산

        # 이미지 크기 조정
        img_resized = img.resize(new_size, Image.LANCZOS)

        # 메모리 버퍼에 리사이즈된 이미지 저장
        img_byte_arr = io.BytesIO()
        img_resized.save(img_byte_arr, format=img.format)
        img_byte_arr.seek(0)
        
        return img_byte_arr  # 형식도 반환


def natural_language_processing(text):
    
    # API 엔드포인트
    url = 'http://3.38.183.235:8001/correct_ingredients/'

    # JSON 데이터
    data = {
        "ingredients": text
    }

    # 요청 헤더
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    # POST 요청 보내기
    response = requests.post(url, json=data, headers=headers)

    # 응답 출력
    return response.json()['corrected_ingredients']      # JSON 형식의 응답 데이터


def draw_boxes_on_image(image_path, ocr_result):

    # ocr_result가 JSON 문자열일 경우, 파이썬 딕셔너리로 변환
    if isinstance(ocr_result, str):
        ocr_result = json.loads(ocr_result)
        
    # 이미지 열기
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    extracted_texts = []  # 추출된 텍스트를 저장할 리스트
    
    # OCR 결과에서 boundingPoly 추출
    for field in ocr_result['images'][0]['fields']:
        vertices = field['boundingPoly']['vertices']
        points = [(vertex['x'], vertex['y']) for vertex in vertices]

        # 사각형 그리기
        draw.polygon(points, outline="red", width=2)

        # OCR 추출된 텍스트 확인
        infer_text = field.get('inferText', '')
        extracted_texts.append(infer_text)  # 텍스트 추가

    # print(extracted_texts)
    # image.show()
    
    return image, extracted_texts
