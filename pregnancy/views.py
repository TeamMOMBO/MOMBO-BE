from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer, OpenApiParameter
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Max, Q

from .models import FAQ, Information
from .serializers import InformationSerializer, FAQSerializer
from .utils import weeks_since
from user.serializers import ProfileSerializer
from user.models import Profile
from ingredient.models import Ingredient
from ingredient.serializers import IngredientSerializer
import random
import pandas as pd


from django.contrib.auth import get_user_model
User = get_user_model()

# Create your views here.

class Home(APIView):
    # permission_classes = [IsAuthenticated]
    @extend_schema(
        summary="메인페이지 API",
        description="메인페이지 API에 대한 설명 입니다.",
        parameters=[],
        tags=["Ingredient"],
        responses=InformationSerializer,
        examples=[
            OpenApiExample(
                response_only=True,
                name="200_OK",
                value={
                        "user": {
                            "id": 1,
                            "nickname": "닉네임",
                            "userType": "임신부",
                            "pregnancyDate": "2024-10-01T19:14:18+09:00",
                            "pregnancyWeek": 1,
                            "email": "test@gmail.com"
                        },
                        "weekInformation": {
                            "id": 4,
                            "step": "초기",
                            "week": 6,
                            "fetus": "초음파로 배아의 심장박동이 뛰는 것을 볼 수 있습니다. ...",
                            "maternity": "임신하면 호르몬의 영향으로 자궁으로 가는 혈액의 양이 늘어나고 ...",
                            "summary": "호르몬의 변화로 자궁에 가는 혈액이 늘어나고 대사가 활발해져요. ..."
                        },
                        "faqs": [
                            {
                                "id": 114,
                                "question": "임신 중 배 뭉침이 너무 잦아서 걱정입니다.",
                                "real_question": "임신 29주 때 배 뭉침이 잦아서 문의 드렸는데, ...",
                                "answer": "자궁 경부 길이가 짧아졌다는 것은 조기 진통 ...",
                                "views": 0
                            },
                            {
                                "id": 166,
                                "question": "[모유수유와 생리] 모유수유중에는 생리를 안하나요?",
                                "real_question": "아이가 돌이 지나 곧 수유를 중단하려고 ..",
                                "answer": "모유수유중인 엄마에서도 분만 3주 후 부터는 모유수는 ...",
                                "views": 0
                            },
                            {
                                "id": 212,
                                "question": "[2차성 불임증] 출산한지 2년이 넘었는데 둘째 아이가 안 생겨요",
                                "real_question": "저는 첫째아이를 출산한지 2년이 넘었습니다. ...",
                                "answer": "처음부터 아예 임신이 되지 않은 것이 아니고 ...",
                                "views": 0
                            }
                        ]
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
    def get(self, request):
        
        try:
            # user = request.user
            user = User.objects.get(id=1)
        except:
            Response({'message':'401_UNAUTHORIZED'}, status=status.HTTP_401_UNAUTHORIZED)

        # 프로필 가져오기
        profile = Profile.objects.get(user=user)
        profileSerializer = ProfileSerializer(profile) # 프로필 직렬화

        # 주차별 정보 가져오기 / pregnancyDate로 주차 계산
        weekInformation = Information.objects.get(week=weeks_since(profileSerializer.data['pregnancyDate']))
        weekInformationSerializer = InformationSerializer(weekInformation)

        # 모든 FAQ 가져와서 랜덤 3개 추출
        max_id = FAQ.objects.all().aggregate(max_id=Max("id"))['max_id'] 
        all_faqlist = [i for i in range(1,max_id+1)] 
        random_faq = random.sample(all_faqlist,3)
        queryset = FAQ.objects.filter(id__in=random_faq)
        faqSerializer = FAQSerializer(queryset, many=True)

        message = {
            "user": profileSerializer.data,
            "weekInformation": weekInformationSerializer.data,
            "faqs": faqSerializer.data
        }

        return Response(message, status=status.HTTP_200_OK)


class Search(APIView):
    @extend_schema(
        summary="검색 결과 API",
        description="검색 결과 API에 대한 설명 입니다.",
        parameters=[],
        tags=["search"],
        responses=InformationSerializer,
        examples=[
            OpenApiExample(
                response_only=True,
                name="200_OK",
                value={
                        "faqs": [
                            {
                                "id": 114,
                                "question": "임신 중 배 뭉침이 너무 잦아서 걱정입니다.",
                                "real_question": "임신 29주 때 배 뭉침이 잦아서 문의 드렸는데, ...",
                                "answer": "자궁 경부 길이가 짧아졌다는 것은 조기 진통 ...",
                                "views": 0
                            },
                            {
                                "id": 166,
                                "question": "[모유수유와 생리] 모유수유중에는 생리를 안하나요?",
                                "real_question": "아이가 돌이 지나 곧 수유를 중단하려고 ..",
                                "answer": "모유수유중인 엄마에서도 분만 3주 후 부터는 모유수는 ...",
                                "views": 0
                            },
                            {
                                "id": 212,
                                "question": "[2차성 불임증] 출산한지 2년이 넘었는데 둘째 아이가 안 생겨요",
                                "real_question": "저는 첫째아이를 출산한지 2년이 넘었습니다. ...",
                                "answer": "처음부터 아예 임신이 되지 않은 것이 아니고 ...",
                                "views": 0
                            }
                        ]
                    }
            ),
            OpenApiExample(
                response_only=True,
                name="400_BAD_REQUEST",
                value={
                    "message": "키워드가 존재하지 않습니다.",
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
    def get(self, request):
        keyword = request.GET.get('keyword')

        if not keyword:
            return Response({"message":"검색 창이 입력되지 않았습니다."}, status=status.HTTP_400_BAD_REQUEST)

        faqs = FAQ.objects.filter(Q(question__icontains=keyword) | Q(real_question__icontains=keyword)| Q(answer__icontains=keyword)).order_by('-id')
        faqs_serializer = FAQSerializer(faqs, many=True).data
        
        ingredients = Ingredient.objects.filter(Q(ingredientKr__icontains=keyword)).order_by('-id')
        ingredients_serializer = IngredientSerializer(ingredients, many=True).data
        
        response_data = {
            "faqs" : faqs_serializer,
            "ingredients" : ingredients_serializer,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class FAQUploadAPIView(APIView):
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
        faqs = []
        for _, row in data.iterrows():
            faqs.append(FAQ(
                question = row.iloc[0],
                real_question = row.iloc[1],
                answer = row.iloc[2],
                views = 0
            ))
        
        FAQ.objects.bulk_create(faqs)

        return Response({"message": "데이터가 성공적으로 업로드되었습니다."}, status=status.HTTP_201_CREATED)
    

class InfomationUploadAPIView(APIView):
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
        informations = []
        for _, row in data.iterrows():
            informations.append(Information(
                step = row.iloc[0],
                Week = row.iloc[1],
                fetus = row.iloc[2],
                maternity = row.iloc[3],
                summary = row.iloc[4]
            ))
        
        Information.objects.bulk_create(informations)

        return Response({"message": "데이터가 성공적으로 업로드되었습니다."}, status=status.HTTP_201_CREATED)