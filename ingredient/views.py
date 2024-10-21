from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from json.decoder import JSONDecodeError
from .serializers import IngredientSerializer, UserAnalysisResultSerializer, IngredientResultSerializer
from django.db.models import Q
from .models import Ingredient, UserAnalysisResult, IngredientResult
from .imgUpload import S3ImgUploader
from .ocr import OCR
from .utils import draw_boxes_on_image, natural_language_processing, resize_image_width
from user.serializers import ProfileSerializer
from user.models import Profile
import pandas as pd
import dotenv
import os
import requests

import time

from django.contrib.auth import get_user_model

User = get_user_model()

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
        user = User.objects.get(pk=1)
        profile = Profile.objects.get(user=user)
        serializer = ProfileSerializer(profile)  # 프로필 직렬화
        
        req_img = request.FILES['image']
        resize_image = resize_image_width(req_img, 1024)
        
        ocr = OCR(resize_image)
        ocr_result = ocr.scanText()
        
        img, text = draw_boxes_on_image(resize_image, ocr_result)
        nlp_result = natural_language_processing(text)
        
        user_analysis_result = UserAnalysisResult.objects.create(
            user_id=user,
            image=None,
            elapsed_time=None
        )
        
        uploader = S3ImgUploader(img)
        image_url = uploader.upload(f'{user_analysis_result.id}')
        
        user_analysis_result.image = f'https://mombobucket.s3.ap-northeast-2.amazonaws.com/{image_url}'
        user_analysis_result.save()
        
        matched_ingredients = []
        level_counts = {"1등급": 0, "2등급": 0}
        
        for term in nlp_result:
            try:
                match = Ingredient.objects.get(ingredientKr__exact=term)
                matched_ingredients.append({
                    'id': match.id,
                    'name': match.ingredientKr,
                    'reason': match.reason,
                    'level': match.level,
                })
                
                if match.level in level_counts:
                    level_counts[match.level] += 1
                
                IngredientResult.objects.create(
                    uar_id=user_analysis_result,
                    ingredient_id=match
                )
            except Exception as e:
                continue
        
        # 위험 수준 결정
        if level_counts["1등급"] > 0:
            riskLevel = "high"
        elif level_counts["2등급"] > 0:
            riskLevel = "middle"
        else:
            riskLevel = "low"
            
        sorted_ingredients = sorted(matched_ingredients, key=lambda x: x['level'])

        message = {
            "riskLevel": riskLevel,
            "user" : serializer.data,
            "analysisImage" : f'https://mombobucket.s3.ap-northeast-2.amazonaws.com/{image_url}',
            "riskIngredientCount": {
                'total': level_counts["1등급"] + level_counts["2등급"],
                '1등급':level_counts["1등급"],
                '2등급':level_counts["2등급"],
                },
            "ingredientAnalysis": sorted_ingredients
        }

        return Response(message, status=status.HTTP_200_OK)
    
    
class IngredientUploadAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "파일이 제공되지 않았습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 파일 확장자에 따라 pandas로 파일 읽기
        if file.name.endswith('.csv'):
            data = pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            data = pd.read_excel(file)
        else:
            return Response({"error": "지원되지 않는 파일 형식입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 데이터 저장
        ingredients = []
        for _, row in data.iterrows():
            ingredients.append(Ingredient(
                categoryId = row.iloc[0],
                effectType = row.iloc[1],
                ingredientKr = row.iloc[2],
                ingredient = row.iloc[3],
                level = row.iloc[4],
                reason = row.iloc[5],
                notes = row.iloc[6]
            ))
        
        Ingredient.objects.bulk_create(ingredients)

        return Response({"message": "데이터가 성공적으로 업로드되었습니다."}, status=status.HTTP_201_CREATED)