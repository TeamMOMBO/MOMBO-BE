from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth import logout
from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer, ProfileSerializer
from .models import Profile, User
from .utils import set_to_next_monday
from pregnancy.utils import weeks_since
from ingredient.models import Ingredient, UserAnalysisResult, IngredientResult
from ingredient.serializers import IngredientSerializer, UserAnalysisResultSerializer, IngredientResultSerializer
import dotenv
import os
import requests

dotenv.load_dotenv()

CALLBACK_URI = 'https://api.mombo.site/user/login/kakao/callback/'
KAKAO_REST_API_KEY = os.environ['KAKAO_REST_API_KEY']
STATE = os.environ['STATE']


class Login(APIView):
    @extend_schema(
        summary="카카오 로그인 API",
        description="카카오 로그인에 대한 설명 입니다.",
        parameters=[],
        tags=["User"],
        responses=ProfileSerializer,
        request=inline_serializer(
            name="KakaoCallback",
            fields={
                "code": serializers.CharField(),
            },
        ),
        examples=[
            OpenApiExample(
                response_only=True,
                name="가입이력있음",
                value={
                    "status": 200,
                    "res_data": {
                        "message": "Login success",
                        "token": {
                            "access": "eyJhbGci123213iIqwesInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjo...",
                            "refresh": "eyJhbGc123424zI1NasiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBl..."
                        }
                    },
                }
            ),
            OpenApiExample(
                response_only=True,
                name="가입이력없음",
                value={
                    "status": 200,
                    "res_data": {
                        "email": "test@gmail.com",
                        "message": "프로필 생성 진행"
                        
                    },
                }
            ),
            OpenApiExample(
                response_only=True,
                name="400_BAD_REQUEST",
                value={
                    "status": 400,
                    "res_data": {
                        "error": f"failed to get email"
                    },
                }
            ),
            OpenApiExample(
                response_only=True,
                name="400_BAD_REQUEST",
                value={
                    "status": 400,
                    "res_data": {
                        "error": f"This AccessToken Doses Not Exist"
                    },
                }
            ),
        ],
    )
    def get(self, request):
        code = request.query_params.get('code')

        # body에 해당 값을 포함시켜서 보내는 부분입니다.
        request_data = {
            'grant_type': 'authorization_code',
            'client_id': KAKAO_REST_API_KEY,
            'redirect_uri': CALLBACK_URI,
            'code': code,
        }
        
        # header에 content-type을 지정해주는 부분입니다.
        token_headers = {
            'Content-type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
        token_res = requests.post("https://kauth.kakao.com/oauth/token", data=request_data, headers=token_headers)
        
        token_json = token_res.json()
        access_token = token_json.get('access_token')

        if not access_token:
            return Response({'error': 'This AccessToken Doses Not Exist'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            auth_headers = {
                "Authorization": f'Bearer ${access_token}',
                "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
            }

            user_info_res = requests.post("https://kapi.kakao.com/v2/user/me", headers=auth_headers)
            user_info_json = user_info_res.json()

            kakao_account = user_info_json.get('kakao_account')

            if not kakao_account:
                return Response({'error': 'failed to get email'}, status=status.HTTP_400_BAD_REQUEST)
            
            email = kakao_account.get('email')

            try:
                user = User.objects.get(email=email)

                token = RefreshToken.for_user(user)
                access_token = str(token.access_token)
                refresh_token = str(token)
                
                # return HttpResponseRedirect(f"http://localhost:3000/login/redirection?isMember=true&accessToken={access_token}&refreshToken={refresh_token}")
                # return HttpResponseRedirect(f"http://192.168.1.16:3000/login/redirection?isMember=true&accessToken={access_token}&refreshToken={refresh_token}")
                return HttpResponseRedirect(f"https://www.mombo.site/login/redirection?isMember=true&accessToken={access_token}&refreshToken={refresh_token}")
            except User.DoesNotExist:
                # return HttpResponseRedirect(f"http://localhost:3000/login/redirection?isMember=false&email={email}")
                # return HttpResponseRedirect(f"http://192.168.1.16:3000/login/redirection?isMember=false&email={email}")
                return HttpResponseRedirect(f"https://www.mombo.site/login/redirection?isMember=false&email={email}")


class Join(APIView):
    @extend_schema(
        summary="회원가입 API",
        description="회원가입 API에 대한 설명 입니다.",
        parameters=[],
        tags=["User"],
        responses=inline_serializer(
            name="Join_API",
            fields={
                "email": serializers.CharField(),
                "nickname": serializers.CharField(),
                "userType": serializers.CharField(),
                "pregnancyWeek": serializers.IntegerField(),
            },
        ),
        request=inline_serializer(
            name="Join_API",
            fields={
                "email": serializers.CharField(),
                "nickname": serializers.CharField(),
                "userType": serializers.CharField(),
                "pregnancyWeek": serializers.IntegerField(),
            },
        ),
        examples=[
            OpenApiExample(
                response_only=True,
                name="200_OK",
                value={
                    "status": 200,
                    "res_data": {
                        "message": "회원가입 성공",
                        "token": {
                            "access": "eyJhbGci123213iIqwesInR5cCI6IkpXVCJ9.eyJ0b...",
                            "refresh": "eyJhbGc123424zI1NasiIsInR5cCI6IkpXVCJ9.eyJ..."
                        }
                    },
                }
            ),
            OpenApiExample(
                response_only=True,
                name="400_BAD_REQUEST",
                value={
                    "status": 400,
                    "res_data": {"error": "프로필 정보를 입력해주세요."},
                },
            ),
            OpenApiExample(
                response_only=True,
                name="400_BAD_REQUEST",
                value={
                    "status": 400,
                    "res_data": {"error": "serializer.errors"},
                },
            ),
        ],
    )
    def post(self, request):
        try:
            user = User.objects.create(email=request.data.get('email'))
            user.set_unusable_password()
            user.save()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            profile = Profile.objects.get(user=user)
            
            nickname = request.data.get('nickname')
            userType = request.data.get('userType')
            pregnancyWeek = request.data.get('pregnancyWeek')
            
            profile_data = {
                "user": user.id,
                "nickname": nickname,
                "userType": userType,
            }
            
            if pregnancyWeek != 0:
                profile_data["pregnancyDate"] = set_to_next_monday(pregnancyWeek)

            pf_serializer = ProfileSerializer(profile, profile_data)

            if pf_serializer.is_valid():
                pf_serializer.save()
            else:
                return Response(pf_serializer.errors,status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken.for_user(user)
            access_token = str(token.access_token)
            refresh_token = str(token)

            message = {
                "message": "회원가입 성공",
                "user" : pf_serializer.data,
                "token" : {               
                    "access": access_token,
                    "refresh": refresh_token,
                }
            }

            return Response(message, status=status.HTTP_200_OK)


class Logout(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary="로그아웃 API",
        description="로그아웃 API에 대한 설명 입니다.",
        parameters=[],
        tags=["User"],
        responses=UserSerializer,
        examples=[
            OpenApiExample(
                response_only=True,
                name="200_OK",
                value={
                    "status": 200,
                    "res_data": {
                        "message": "로그아웃 성공",
                    },
                }
            ),
        ],
    )
    def post(self, request):
        user = request.user
        refresh_token = RefreshToken.for_user(user)
        refresh_token.blacklist()
        logout(request)
        return Response({"message":"로그아웃 성공"},status=status.HTTP_200_OK)


# 프로필 조회
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary="프로필 조회 API",
        description="프로필 조회 API에 대한 설명 입니다.",
        parameters=[],
        tags=["Profile"],
        responses=inline_serializer(
            name="Get_Profile",
            fields={
                "profile": serializers.CharField(),
            },
        ),
        examples=[
            OpenApiExample(
                response_only=True,
                name="200_OK",
                value={
                    "status": 200,
                    "res_data": {
                        "profile": {
                            "id": 2,
                            "email": "test@gmail.com",
                            "nickname": "테스트",
                            "userType": "테스트",
                            "pregnancyDate": '2024-11-01',
                            "pregnancyWeek": 1,
                        },
                        "userAnalysisResult": [{"id": 1,
                                    "user_id": 2,
                                    "image": "image/url",
                                    "elapsed_time": 30,
                                    "created_at": "2024-09-26T21:10:05.460483+09:00",
                                    }],
                    },
                }
            ),
            OpenApiExample(
                response_only=True,
                name="404_NOT_FOUND",
                value={
                    "status": 404,
                    "res_data": {"error": "프로필 정보를 찾을 수 없습니다."},
                },
            ),
        ],
    )
    def get(self, request):
        
        try:
            user = request.user
        except:
            Response({"message": "유저 정보를 찾을 수 없습니다."}, status=status.HTTP_401_UNAUTHORIZED)
        
        profile = get_object_or_404(Profile, user=user)
        pf_serializer = ProfileSerializer(profile, context={'request':request})
        
        profile_data = pf_serializer.data
        
        if profile_data['pregnancyDate']:
            pregnancyWeek = weeks_since(profile_data['pregnancyDate'])
        else:
            pregnancyWeek = 0
            
        profile_data['pregnancyWeek'] = pregnancyWeek
        
        # 해당 user의 성분 분석 결과를 가져오기
        user_analysis_results = UserAnalysisResult.objects.filter(user_id=user)
        user_analysis_results_serializer = UserAnalysisResultSerializer(user_analysis_results, many=True)

        data = {
            "profile": profile_data,
            "user_analysis_results": user_analysis_results_serializer.data  # 성분 분석 결과 추가
        }

        return Response(data, status=status.HTTP_200_OK)


# 프로필 수정
class ProfileEditView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    @extend_schema(
        summary="프로필 수정 API",
        description="프로필 수정 API에 대한 설명 입니다.",
        parameters=[],
        tags=["Profile"],
        responses=inline_serializer(
            name="Profile_Edit_API",
            fields={
                "nickname": serializers.CharField(),
                "userType": serializers.CharField(),
                "pregnancyWeek": serializers.IntegerField(),
            },
        ),
        request=inline_serializer(
            name="Profile_Edit_API",
            fields={
                "nickname": serializers.CharField(),
                "userType": serializers.CharField(),
                "pregnancyWeek": serializers.IntegerField(),
            },
        ),
        examples=[
            OpenApiExample(
                response_only=True,
                name="200_OK",
                value={
                    "status": 200,
                    "res_data": {
                        "message": "프로필 수정이 완료되었습니다."
                    },
                }
            ),
            OpenApiExample(
                response_only=True,
                name="404_NOT_FOUND",
                value={
                    "status": 404,
                    "res_data": {"error": "프로필 정보를 찾을 수 없습니다."},
                },
            ),
            OpenApiExample(
                response_only=True,
                name="400_BAD_REQUEST",
                value={
                    "status": 400,
                    "res_data": {"error": "올바르지 않은 프로필 데이터입니다."},
                },
            ),
        ],
    )
    def put(self, request):
        profile = request.user.profile
        
        pregnancyWeek = request.data.get('pregnancyWeek')
        userType = request.data.get('userType')
        nickname = request.data.get('nickname')
        
        # pregnancyWeek를 숫자형으로 변환 (예외 처리 추가)
        try:
            pregnancyWeek = int(pregnancyWeek) if pregnancyWeek is not None else 0
        except ValueError:
            return Response({"error": "pregnancyWeek는 숫자여야 합니다."}, status=status.HTTP_400_BAD_REQUEST)

        # pregnancyWeek가 0일 경우 None (null)로 설정
        if pregnancyWeek == 0:
            pregnancyDate = None
        else:
            pregnancyDate = set_to_next_monday(pregnancyWeek)

        edit_data = {
            'pregnancyDate': pregnancyDate,
            'userType': userType,
            'nickname': nickname
        }

        serializer = ProfileSerializer(profile, data=edit_data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "프로필 수정이 완료되었습니다."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Withdrawal(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        summary="회원 탈퇴 API",
        description="회원 탈퇴 API에 대한 설명 입니다.",
        parameters=[],
        responses=UserSerializer,
        tags=["User"],
        examples=[
            OpenApiExample(
                response_only=True,
                name="200_OK",
                value={
                    "status": 200,
                    "res_data": {
                        "message": "회원탈퇴 되었습니다."
                    },
                }
            ),
        ],
    )
    def delete(self, request):
        user = request.user
        provided_password = request.data.get('password', None)
        if not provided_password or not check_password(provided_password, user.password):
            return Response({"error": "비밀번호가 정확하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        refresh_token = RefreshToken.for_user(user)
        refresh_token.blacklist()
        
        profile = user.profile
        profile.nickname =f'deleteuser_{profile.id}'
        profile.save()
        
        user.is_active = False
        user.save()
            
        return Response({"message": "회원탈퇴 되었습니다."}, status=status.HTTP_200_OK)
