from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer, OpenApiParameter, OpenApiResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import IngredientSerializer, UserAnalysisResultSerializer, IngredientResultSerializer
from .models import Ingredient, UserAnalysisResult, IngredientResult
from .imgUpload import S3ImgUploader
from .ocr import OCR
from .utils import draw_boxes_on_image, natural_language_processing, resize_image_width
from user.serializers import ProfileSerializer
from user.models import Profile
import pandas as pd

from django.contrib.auth import get_user_model

User = get_user_model()

# 페이징 처리 클래스
class IngredientPagination(PageNumberPagination):
    page_size = 20  # 한 페이지에 20개 항목
    page_size_query_param = 'page_size'
    max_page_size = 100  # 최대 페이지 크기 제한


class Dictionary(APIView):
    @extend_schema(
        summary="성분 사전 API",
        description="성분 사전 API에 대한 설명 입니다. 주어진 정렬 방법에 따라 성분 리스트를 반환합니다.",
        parameters=[
            OpenApiParameter(
                name='sort', 
                description="정렬 기준", 
                required=True, 
                type=str,
                enum=[ 'name', 'level']  # 선택 가능한 값 제한
            ),
            OpenApiParameter(name='page', description='페이지 번호 (정수 값)', required=False, type=int),
            OpenApiParameter(
                name='order', 
                description="정렬 순서", 
                required=False, 
                type=str,
                enum=[ 'asc', 'desc']  # 선택 가능한 값 제한
            )
        ],
        tags=["Ingredient"],
        responses={
            200: OpenApiResponse(
                response=IngredientSerializer,
                description="성분 사전 API.",
                examples=[
                    OpenApiExample(
                        name="200_OK",
                        value={
                            "ingredients": [
                                {
                                    "id": 1,
                                    "ingredientKr": "성분 예시",
                                    "ingredientDescription": "이 성분은 예시 설명입니다."
                                }
                            ]
                        },
                    ),
                    OpenApiExample(
                        name="400_BAD_REQUEST",
                        value={
                            "message": "정렬 방법이 없습니다.",
                        },
                    ),
                    OpenApiExample(
                        name="401_UNAUTHORIZED",
                        value={
                            "message": "401_UNAUTHORIZED",
                        },
                    ),
                ],
            )
        },
    )
    def get(self, request):
        # sort와 page 파라미터 받기
        sort = request.GET.get('sort')
        page = int(request.GET.get('page', 1))
        order = request.GET.get('order', 'asc')  # 'asc' is the default

        if not sort:
            return Response({"message": "정렬 방법이 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 정렬 기준에 따른 QuerySet 처리
        if sort == 'name':
            if order == 'desc':
                ingredients = Ingredient.objects.all().order_by('-ingredientKr')  # 기준 내림차순
            else:
                ingredients = Ingredient.objects.all().order_by('ingredientKr')  # 기준 오름차순
        elif sort == 'level':
            if order == 'desc':
                ingredients = Ingredient.objects.all().order_by('-level')  # 내림차순
            else:
                ingredients = Ingredient.objects.all().order_by('level')  # 오름차순
        else:
            return Response({"message": "잘못된 정렬 기준입니다."}, status=status.HTTP_400_BAD_REQUEST)


        # 페이징 처리
        paginator = IngredientPagination()
        paginated_ingredients = paginator.paginate_queryset(ingredients, request)

        ingredients_serializer = IngredientSerializer(paginated_ingredients, many=True).data
        maxPage = (ingredients.count() + paginator.page_size - 1) // paginator.page_size

        response_data = {
            "ingredients": ingredients_serializer,
            "count": ingredients.count(),  # 총 항목 수
            "page": page,
            "page_size": paginator.page_size,
            "maxPage": maxPage,
        }

        return paginator.get_paginated_response(response_data)


class IngredientAnalysis(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
    summary="성분분석 API",
    description="성분분석 API에 대한 설명입니다. 이 API는 이미지를 업로드하여 성분을 분석합니다.",
    parameters=[
        OpenApiParameter(
            name='Content-Type',
            location=OpenApiParameter.HEADER,
            description="요청의 Content Type, 일반적으로 이미지를 전송할 때는 'multipart/form-data'를 사용합니다.",
            required=True,
            type=str,
            default='multipart/form-data'
        ),
    ],
    tags=["Ingredient"],
    responses=UserAnalysisResultSerializer,
    request=inline_serializer(
        name="Ingredient_API",
        fields={
            "image": serializers.FileField(required=True),  # 필수로 설정
        },
    ),
    examples=[
        OpenApiExample(
            response_only=True,
            name="200_OK",
            value={
                "riskLevel": "high",  # low - middle - high 3단계로 구성
                "user": {"userNo": 0, 'email': 'test@email.com'},  # 유저 정보
                "analysisImage": "image/AWS_S3_URL",  # S3 이미지 URL
                "riskIngredientCount": {
                    'total': 8,
                    '1단계': 4,
                    '2단계': 1,
                },
                "ingredientAnalysis": [{
                    'id': 0,
                    'name': '아세클로페낙',
                    'level': '2단계',
                    'reason': '''임부에 대한 안전성 미확립.
                    임신 말기에 투여시 태아의 동맥관조기폐쇄 가능성.
                    동물실험에서 비스테로이드성 소염진통제는 난산발생빈도 증가, 분만지연, 태아 생존율 감소 보고.
                    임신 약 20주 이후 비스테로이드성 소염제의 사용은 태아의 신기능 이상을 일으켜 양수 과소증 유발 가능 및 경우에 따라 신생아 신장애 발생 가능'''
                }, {
                    'id': 1,
                    'name': '3´-데옥시-3´-플루오로티미딘(18F)',
                    'level': '2단계',
                    'reason': '임부에 대한 안전성 미확립.'
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
        OpenApiExample(
            response_only=True,
            name="401_UNAUTHORIZED",
            value={
                "message": "401_UNAUTHORIZED",
            },
        ),
    ],
    )
    def post(self, request):

        try:
            user = request.user
        except:
            Response({"error": "유저를 찾을 수 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        profile = Profile.objects.get(user=user)
        serializer = ProfileSerializer(profile)  # 프로필 직렬화
        
        req_img = request.FILES['image']
        resize_image = resize_image_width(req_img, 1024)
        
        ocr = OCR(resize_image)
        ocr_result = ocr.scanText()
        
        img, text = draw_boxes_on_image(resize_image, ocr_result)
        nlp_result = natural_language_processing(text)
        nlp_set = list(set(nlp_result))
        
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
        
        for term in nlp_set:
            try:
                match = Ingredient.objects.get(ingredientKr__exact=term)
                match_data_serializer = IngredientSerializer(match)
                matched_ingredients.append(match_data_serializer.data)
                
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


class AnalysisDetail(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
    summary="성분 분석 결과를 가져오는 API",
    description="성분 분석 결과 API에 대한 설명입니다. 성분 분석 결과를 전달합니다.",
    parameters=[
        OpenApiParameter(
            name='uarNo', 
            description="UAR No", 
            required=True, 
            type=int,
        ),
    ],
    tags=["Ingredient"],
    responses=UserAnalysisResultSerializer,
    examples=[
        OpenApiExample(
            response_only=True,
            name="200_OK",
            value={
                "riskLevel": "high",  # low - middle - high 3단계로 구성
                "analysisImage": "image/AWS_S3_URL",  # S3 이미지 URL
                "riskIngredientCount": {
                    'total': 8,
                    '1단계': 4,
                    '2단계': 1,
                },
                "ingredientAnalysis": [{
                    'id': 0,
                    'name': '아세클로페낙',
                    'level': '2단계',
                    'reason': '''임부에 대한 안전성 미확립.
                    임신 말기에 투여시 태아의 동맥관조기폐쇄 가능성.
                    동물실험에서 비스테로이드성 소염진통제는 난산발생빈도 증가, 분만지연, 태아 생존율 감소 보고.
                    임신 약 20주 이후 비스테로이드성 소염제의 사용은 태아의 신기능 이상을 일으켜 양수 과소증 유발 가능 및 경우에 따라 신생아 신장애 발생 가능'''
                }, {
                    'id': 1,
                    'name': '3´-데옥시-3´-플루오로티미딘(18F)',
                    'level': '2단계',
                    'reason': '임부에 대한 안전성 미확립.'
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
        OpenApiExample(
            response_only=True,
            name="401_UNAUTHORIZED",
            value={
                "message": "401_UNAUTHORIZED",
            },
        ),
        OpenApiExample(
            response_only=True,
            name="404_UNAUTHORIZED",
            value={
                "message": "HTTP_404_NOT_FOUND",
            },
        ),
    ],
    )
    def get(self, request):

        try:
            user = request.user
        except AttributeError:
            return Response({"error": "유저를 찾을 수 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        # sort와 page 파라미터 받기
        uar_id = request.GET.get('uarNo')

        if not uar_id:
            return Response({"error": "UAR 번호가 제공되지 않았습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_analysis_result = UserAnalysisResult.objects.get(pk=uar_id)
        except UserAnalysisResult.DoesNotExist:
            return Response({"error": "해당 분석 결과를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        
        if user_analysis_result.user_id.id != user.id:
            return Response({"error": "접근 권한이 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        ingredient_list = IngredientResult.objects.filter(uar_id=uar_id)
        ir_serializer = IngredientResultSerializer(ingredient_list,many=True).data

        matched_ingredients = []
        level_counts = {"1등급": 0, "2등급": 0}

        for ir in ir_serializer:
            try:
                match = Ingredient.objects.get(pk=ir['ingredient_id'])
                match_data_serializer = IngredientSerializer(match)
                matched_ingredients.append(match_data_serializer.data)

                if match.level in level_counts:
                    level_counts[match.level] += 1

            except Ingredient.DoesNotExist:
                continue

        # Determine risk level based on ingredient levels
        if level_counts["1등급"] > 0:
            risk_level = "high"
        elif level_counts["2등급"] > 0:
            risk_level = "middle"
        else:
            risk_level = "low"

        # Sort the ingredients by level
        sorted_ingredients = sorted(matched_ingredients, key=lambda x: x['level'])

        # Assuming 'image_url' is defined somewhere in the code; otherwise, it should be handled properly.
        message = {
            "riskLevel": risk_level,
            "analysisImage": user_analysis_result.image,
            "riskIngredientCount": {
                'total': level_counts["1등급"] + level_counts["2등급"],
                '1등급': level_counts["1등급"],
                '2등급': level_counts["2등급"],
            },
            "ingredientAnalysis": sorted_ingredients
        }

        return Response(message, status=status.HTTP_200_OK)
    

class IngredientUploadAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    @extend_schema(exclude=True)
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