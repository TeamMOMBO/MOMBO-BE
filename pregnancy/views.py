from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer, OpenApiParameter, OpenApiResponse
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from django.db.models import Max, Q
from rest_framework.permissions import IsAuthenticated, AllowAny
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

# 페이징 처리 클래스
class SearchPagination(PageNumberPagination):
    page_size = 20  # 한 페이지에 20개 항목
    page_size_query_param = 'page_size'
    max_page_size = 100  # 최대 페이지 크기 제한
    

class Home(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary="메인페이지 API",
        description="메인페이지 API에 대한 설명 입니다.",
        parameters=[],
        tags=["Home"],
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
            user = request.user
        except:
            return Response({'message':'401_UNAUTHORIZED'}, status=status.HTTP_401_UNAUTHORIZED)

        # 프로필 가져오기
        profile = Profile.objects.get(user=user)
        profileSerializer = ProfileSerializer(profile) # 프로필 직렬화
        
        if profileSerializer.data['pregnancyDate']:
            
            pregnancyWeek = weeks_since(profileSerializer.data['pregnancyDate'])
            
            if pregnancyWeek < 3:
                pregnancyWeek = 3
                
            weekInformation = Information.objects.get(week=pregnancyWeek)
        else:
            random_number = random.randint(3, 40)
            weekInformation = Information.objects.get(week=random_number)
            
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
        parameters=[
            OpenApiParameter(name='keyword', description='검색어', required=True, type=str),
        ],
        tags=["Search"],
        responses={
            200: OpenApiResponse(
                response=InformationSerializer,
                description="검색 결과를 반환합니다.",
                examples=[
                    OpenApiExample(
                        name="200_OK",
                        value={
                            "faqs": [
                                {
                                    "id": 114,
                                    "question": "임신 중 배 뭉침이 너무 잦아서 걱정입니다.",
                                    "real_question": "임신 29주 때 배 뭉침이 잦아서 문의 드렸는데, ...",
                                    "answer": "자궁 경부 길이가 짧아졌다는 것은 조기 진통 ...",
                                    "views": 0
                                }
                            ],
                            "faqsCount":1,
                            "ingredients": [
                                {
                                    "id": 1,
                                    "ingredientKr": "성분 예시",
                                    "ingredientDescription": "이 성분은 예시 설명입니다."
                                }
                            ],
                            "ingredientsCount":1,
                        },
                    ),
                    OpenApiExample(
                        name="400_BAD_REQUEST",
                        value={
                            "message": "검색 창이 입력되지 않았습니다.",
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
        keyword = request.GET.get('keyword')

        if not keyword:
            return Response({"message": "검색 창이 입력되지 않았습니다."}, status=status.HTTP_400_BAD_REQUEST)

        # FAQ
        faqs_queryset = FAQ.objects.filter(
            Q(question__icontains=keyword) | Q(real_question__icontains=keyword) | Q(answer__icontains=keyword)
        )
        faqs_count = faqs_queryset.count()
        faqs = faqs_queryset.order_by('-id')[:3]
        faqs_serializer = FAQSerializer(faqs, many=True).data

        # Ingredient
        ingredients_queryset = Ingredient.objects.filter(Q(ingredientKr__icontains=keyword))
        ingredients_count = ingredients_queryset.count()
        ingredients = ingredients_queryset.order_by('-id')[:3]
        ingredients_serializer = IngredientSerializer(ingredients, many=True).data
        
        response_data = {
            "faqs": faqs_serializer,
            "faqsCount": faqs_count,
            "ingredients": ingredients_serializer,
            "ingredientsCount": ingredients_count
        }

        return Response(response_data, status=status.HTTP_200_OK)


class SearchDetail(APIView):
    @extend_schema(
        summary="검색 결과 디테일 API",
        description="검색 결과 디테일 API에 대한 설명 입니다. 주어진 키워드에 따라 FAQ와 성분 정보를 검색하여 반환합니다.",
        parameters=[
            OpenApiParameter(name='keyword', description='검색어', required=True, type=str),
            OpenApiParameter(name='page', description='페이지 번호 (정수 값)', required=False, type=int),
            OpenApiParameter(
                name='category', 
                description="검색 카테고리 (가능한 값: 'content', 'ingredient')", 
                required=False, 
                type=str,
                enum=[ 'content', 'ingredient']  # 선택 가능한 값 제한
            )
        ],
        tags=["Search"],
        responses={
            200: OpenApiResponse(
                response=InformationSerializer,
                description="검색 결과를 반환합니다.",
                examples=[
                    OpenApiExample(
                        name="200_OK",
                        value={
                            "count": 2,
                            "next": None,
                            "previous": None,
                            "results": {
                                "category": [
                                {
                                    "id": 223,
                                    "question": "출산 후 호박 달인 물은 언제 먹어야  하나요?",
                                    "real_question": "분만하고 몸조리할 때 부기 빠지라고 호박 달인 물을 먹는데 애 낳고 바로 먹어야 하는지 것인지 아니면 삼칠일이지나서 마셔야 하는지 궁금해요.",
                                    "answer": "「산모에게 늙은 호박이 좋다.」라는 구전은 호르몬의 변화가 정상으로 돌아온 뒤, 즉 출산 후 한 달이 지나서도 배뇨에 이상이 있거나 다리 쪽 부종이 심한 경우에 적용한 것에서 비롯된 것이라고 볼 수 있습니다. 유의해야 할 것은 출산 직후 생기는 부종은 신장이 나빠서가 아니라 임신 중 피부에 축적된 수분 때문입니다. 분만이 다가오면 임신부의 몸은 출혈과 수분 손실을 대비하기 위해서 호르몬의 작용으로 충분한 수분을 보관합니다. 그리고 아기를 낳고",
                                    "views": 0,
                                    "image": "https://i.ibb.co/CQQ4rBK/suhyeon-choi-NIZeg731-Lx-M-unsplash.jpg"
                                },
                                {
                                    "id": 52,
                                    "question": "임신 중에 음식 섭취를 어떻게 해야 하나요?",
                                    "real_question": "이제 20주 된 아기를 가진 예비 아빠입니다. 음식에 대해 궁금한 점이 몇 가지 있습니다. 아내는 음식 때문에 스트레스를 좀 받고 있습니다. 좋아하는 음식(우유, 고구마)이 몸에 해롭지 않음에도 주위에서 아기에게 아토피를 일으킨다고 해서 먹어야 할지 말아야 할 지 고민을 하고 있더라고요. 아내는 변비 해결을 위해 다시마와 검은깨, 검은콩을 갈아서 매일 아침 우유에 타먹고 다니는데 육아 책을 봐도 우유 섭취에 대한 제약을 하지 않고 있습니다. 그런데 태아에게 아토피를 유발한다면서 자제를 하라고 한다는데, 적당 섭취량과 유기농 우유를 먹어야 하는지 등을 알고 싶습니다. 그리고 호박 고구마를 좋아해서 살도 안찌고 변비에 도움이 되기에 많이 샀는데, 호박고구마가 유전자 조작이 된 거라면서 섭취를 하면 아기가 아토피에 걸린다고 하더라고요. 주위에서는 유기농으로만 먹여야 한다고 하는데 이것도 사실인가요? 경제적으로 부담이 되네요.",
                                    "answer": "임신 시에 가려야 할 음식에 대한 많은 속설이 존재합니다. 또한 물론 산에서 나오고 무농약의 음식들만 먹는다면 좋겠지만, 현대 사회에서 어느 정도의 농약이나 음식에서 나올 수 있는 물질들을 너무 많이 가리는 것은 현실적으로 불가능합니다. 아토피가 있는 산모의 경우 물론 아기가 아토피가 있을 것을 걱정하실 수는 있지만 우유나 콩 등에 평소 알레르기가 있지 않으시다면 드시는 음식을 그냥 드시면 될 것으로 보입니다. 토양이나 어떤 생선에서 나올 수 있다는 이상 물질들이 체내나 태아에게 이상을 일으킬 정도를 섭취하려면 농약지대에서 지속적으로 산다든지 원폭 지역 등 일상적인 지역이 아닌 특수 지역민들을 상대로 한 검사 등을 이야기하는 것이므로 일반적으로 몸에 좋다는 음식 위주의 평범한 식습관으로 골고루 드시는 것이 좋을 것으로 보입니다.  ",
                                    "views": 0,
                                    "image": "https://i.ibb.co/CQQ4rBK/suhyeon-choi-NIZeg731-Lx-M-unsplash.jpg"
                                }
                                ],
                                "count": 2,
                                "page": 1,
                                "page_size": 20,
                                "maxPage": 1
                            }
                        },
                    ),
                    OpenApiExample(
                        name="400_BAD_REQUEST",
                        value={
                            "message": "검색 창이 입력되지 않았습니다.",
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
        keyword = request.GET.get('keyword')
        category = request.GET.get('category')
        page = int(request.GET.get('page', 1))

        if not keyword:
            return Response({"message": "검색 창이 입력되지 않았습니다."}, status=status.HTTP_400_BAD_REQUEST)

        if category == 'content':
            faqs = FAQ.objects.filter(
                Q(question__icontains=keyword) | Q(real_question__icontains=keyword) | Q(answer__icontains=keyword)
            ).order_by('-id')
            
            # 페이징 처리
            paginator = SearchPagination()
            paginated_faqs = paginator.paginate_queryset(faqs, request)

            faqs_serializer = FAQSerializer(paginated_faqs, many=True).data
            maxPage = (faqs.count() + paginator.page_size - 1) // paginator.page_size
            
            response_data = {
                "faqs": faqs_serializer,
                "count": faqs.count(),  # 총 항목 수
                "page": page,
                "page_size": paginator.page_size,
                "maxPage": maxPage,
            }

            return paginator.get_paginated_response(response_data)
        else:
            ingredients = Ingredient.objects.filter(Q(ingredientKr__icontains=keyword)).order_by('-id')
            
            # 페이징 처리
            paginator = SearchPagination()
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


class Content(APIView):
    @extend_schema(
        summary="콘텐츠 API",
        description="콘텐츠 API에 대한 설명 입니다. FAQ와 주차별 정보를 반환합니다.",
        parameters=[
            OpenApiParameter(name='page', description='페이지 번호 (정수 값)', required=False, type=int),
            OpenApiParameter(
                name='category', 
                description="카테고리 (가능한 값: 'all', 'faq', 'info')", 
                required=False, 
                type=str,
                enum=['all', 'faq', 'info']  # 선택 가능한 값 제한
            )
        ],
        tags=["Content"],
        responses={
            200: OpenApiResponse(
                response=InformationSerializer,
                description="콘텐츠를 반환합니다.",
                examples=[
                    OpenApiExample(
                        name="200_OK",
                        value={
                            "weekinformations": [
                                {
                                    "id": 4,
                                    "step": "초기",
                                    "week": 6,
                                    "fetus": "초음파로 배아의 심장박동이 뛰는 것을 볼 수 있습니다. ...",
                                    "maternity": "임신하면 호르몬의 영향으로 자궁으로 가는 혈액의 양이 늘어나고 ...",
                                    "summary": "호르몬의 변화로 자궁에 가는 혈액이 늘어나고 대사가 활발해져요. ..."
                                }
                            ],
                            "faqs": [
                                {
                                    "id": 114,
                                    "question": "임신 중 배 뭉침이 너무 잦아서 걱정입니다.",
                                    "real_question": "임신 29주 때 배 뭉침이 잦아서 문의 드렸는데, ...",
                                    "answer": "자궁 경부 길이가 짧아졌다는 것은 조기 진통 ...",
                                    "views": 0
                                }
                            ]
                        },
                    ),
                    OpenApiExample(
                        name="400_BAD_REQUEST",
                        value={
                            "message": "400_BAD_REQUEST",
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
        category = request.GET.get('category')
        page = int(request.GET.get('page', 1))

        if category == 'all':
            faqs = FAQ.objects.all().order_by('-id')[:3]
            faqs_serializer = FAQSerializer(faqs, many=True).data
            
            weekinformations = Information.objects.all().order_by('-id')[:3]
            weekinformations_serializer = InformationSerializer(weekinformations, many=True).data
            
            response_data = {
                "faqs": faqs_serializer,
                "weekinformations": weekinformations_serializer,
            }

            return Response(response_data, status=status.HTTP_200_OK)
        elif category == 'faq':
            faqs = FAQ.objects.all().order_by('-id')
            
            # 페이징 처리
            paginator = SearchPagination()
            paginated_faqs = paginator.paginate_queryset(faqs, request)

            faqs_serializer = FAQSerializer(paginated_faqs, many=True).data
            maxPage = (faqs.count() + paginator.page_size - 1) // paginator.page_size
            
            response_data = {
                "faqs": faqs_serializer,
                "count": faqs.count(),  # 총 항목 수
                "page": page,
                "page_size": paginator.page_size,
                "maxPage": maxPage,
            }

            return paginator.get_paginated_response(response_data)
        elif category == 'info':
            weekinformations = Information.objects.all().order_by('-id')
            weekinformations_serializer = InformationSerializer(weekinformations, many=True).data
            
            response_data = {
                "weekinformations": weekinformations_serializer,
            }
        else:
            return Response({"error": "유효한 카테고리가 아닙니다."}, status=status.HTTP_400_BAD_REQUEST) 


class FAQUploadAPIView(APIView):
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