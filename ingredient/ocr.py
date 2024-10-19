import dotenv
import requests
import mimetypes
import os

dotenv.load_dotenv()
CLOVA_OCR_SECRET = os.environ['CLOVA_OCR_SECRET']
CLOVA_OCR_URL = os.environ['CLOVA_OCR_URL']


class OCR:
    def __init__(self, file):
        self.file = file

    def scanText(self):
        # InMemoryUploadedFile 객체에서 파일을 가져옴
        file_obj = self.file  # InMemoryUploadedFile 객체
        file_name = 'image.png'  # 원하는 파일 이름 지정
        file_format = file_name.split('.')[-1]  # 파일 형식 추출

        # MIME 타입을 파일 이름으로부터 추론
        mime_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'  # 기본 MIME 타입 설정

        headers = {
            'X-OCR-SECRET': CLOVA_OCR_SECRET,
        }

        # OCR API 요청을 위한 파일과 메시지 데이터 설정
        files = {
            'file': (file_name, file_obj, mime_type)  # 올바른 MIME 타입 사용
        }

        data = {
            'message': f'{{"version": "v2", "requestId": "1234", "timestamp": 1722225600000, "lang": "ko", "images": [{{"format": "{file_format}", "name": "covid_sample"}}]}}'
        }

        # POST 요청 전송
        response = requests.post(CLOVA_OCR_URL, headers=headers, files=files, data=data)

        # 응답 텍스트 반환
        return response.text