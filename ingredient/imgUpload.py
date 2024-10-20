from dotenv import load_dotenv
import mimetypes
from io import BytesIO
import boto3
import uuid
import os
from PIL import Image

load_dotenv()

class S3ImgUploader:
    def __init__(self, file):
        self.file = file

    def upload(self, folder):
        
        url = folder+'/'+uuid.uuid1().hex
        s3r = boto3.resource('s3', aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"), aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"))
        s3r.Bucket(os.environ.get("AWS_STORAGE_BUCKET_NAME")).put_object(Key=url, Body=self.file, ContentType='jpg')
        
        return url

    def delete(self):
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
        )

        try:
            # S3 객체 삭제
            s3_client.delete_object(
                Bucket=os.environ.get("AWS_STORAGE_BUCKET_NAME"),
                Key=str(self.file)  
            )
            return True  
        except Exception as e:
            print("S3 이미지 삭제 실패:", str(e))
            return False
