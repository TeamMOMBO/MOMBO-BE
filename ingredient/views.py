from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from json.decoder import JSONDecodeError
from .serializers import IngredientSerializer, UserAnalysisResultSerializer, IngredientResultSerializer
from django.core.mail import EmailMessage
from .models import Ingredient, UserAnalysisResult, IngredientResult
from .imgUpload import S3ImgUploader
from .ocr import OCR
from .utils import draw_boxes_on_image, natural_language_processing, resize_image_width
import dotenv
import os
import requests

import time

# Create your views here.

class IngredientAnalysis(APIView):
    # permission_classes = [IsAuthenticated]
    @extend_schema(
        summary="성분분석 API",
        description="성분분석 API에 대한 설명 입니다.",
        parameters=[],
        tags=["Ingredient"],
        responses=UserAnalysisResultSerializer,
        request=inline_serializer(
            name="Ingredient_API",
            fields={
                "image": serializers.ImageField(),
            },
        ),
        examples=[
            OpenApiExample(
                response_only=True,
                name="200_OK",
                value={
                    "message": "분석 성공",
                }
            ),
            OpenApiExample(
                response_only=True,
                name="400_BAD_REQUEST",
                value={
                    "message": "400_BAD_REQUEST",
                },
            ),
        ],
    )
    def post(self, request):
        # user = request.user
        
        req_img = request.FILES['image']
        
        resize_image = resize_image_width(req_img, 400)  # 가로를 400px로 줄이기
        
        ocr = OCR(resize_image)
        ocr_result = ocr.scanText()
        
        img, text = draw_boxes_on_image(resize_image, ocr_result)
        nlp_result = natural_language_processing(text)
        
        # uploader = S3ImgUploader(img)
        # image_url = uploader.upload('profile')

        message = {
            "riskLevel": "high", # low - middle - high 3단계로 구성
            "user" : {"userNo": 0,'email': 'test@email.com'}, # 유저 정보
            "analysisImage" : "image/AWS_S3_URL", # S3 이미지 URL
            "riskIngredientCount": {
                'total': 8,
                '1단계':4,
                '2단계':1,
                },
            "ingredientAnalysis": [{
                'id':0,
                'name':'아세클로페낙',
                'level':'2단계',
                'reason':'''임부에 대한 안전성 미확립.
                임신 말기에 투여시 태아의 동맥관조기폐쇄 가능성.
                동물실험에서 비스테로이드성 소염진통제는 난산발생빈도 증가, 분만지연, 태아 생존율 감소 보고.
                임신 약 20주 이후 비스테로이드성 소염제의 사용은 태아의 신기능 이상을 일으켜 양수 과소증 유발 가능 및 경우에 따라 신생아 신장애 발생 가능'''
            },{
                'id':1,
                'name':'3´-데옥시-3´-플루오로티미딘(18F)',
                'level':'2단계',
                'reason':'임부에 대한 안전성 미확립.'
            }]
        }

        return Response(message, status=status.HTTP_200_OK)