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
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from json.decoder import JSONDecodeError
from .serializers import UserSerializer, ProfileSerializer
from django.core.mail import EmailMessage
from .models import Profile, User
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
        tags=["Kakao Login"],
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
                            "access": "eyJhbGci123213iIqwesInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzAxMjcwMDQwLCJpYXQiOjE3MDEyNjI4NDAsImp0aSI6IjAyNjU5NjkwZmM3YjQ3Njg4YzkxZDUxOThiMDNlMjgyIiwidXNlcl9pZCI6Nn0.TjEFfq-K3Q7Ol31roq7MybH7iJ_r9dW0cbUt9cG9Gac",
                            "refresh": "eyJhbGc123424zI1NasiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcwMTM0OTI0MCwiaWF0IjoxNzAxMjYyODQwLCJqdGkiOiIxMzk0ZTdhNWJiM2Y0MzQ0Yjk0OWU3MWYyNDhjMzQ4YyIsInVzZXJfaWQiOjZ9.1eTJK2LgWV8KprCO-HcvaZyg6GjVsnQl7PlkvzuJPhM"
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
                refresh = RefreshToken.for_user(user)
                
                token={
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }
                
                return HttpResponseRedirect(f"http://localhost:3000/login/redirection?isMember=true&accessToken={token.access}&refreshToken={token.refresh}")
                # return HttpResponseRedirect(f"https://www.mombo.site/login/redirection?isMember=true&accessToken={token.access}&refreshToken={token.refresh}")
            except User.DoesNotExist:
                return HttpResponseRedirect(f"http://localhost:3000/login/redirection?isMember=false&email={email}")
                # return HttpResponseRedirect(f"https://www.mombo.site/login/redirection?isMember=false&email={email}")
            

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
                "member_type": serializers.CharField(),
                "pregnancy_date": serializers.IntegerField(),
            },
        ),
        request=inline_serializer(
            name="Join_API",
            fields={
                "email": serializers.CharField(),
                "nickname": serializers.CharField(),
                "member_type": serializers.CharField(),
                "pregnancy_date": serializers.IntegerField(),
            },
        ),
        examples=[
            OpenApiExample(
                response_only=True,
                name="200_OK",
                value={
                    "status": 200,
                    "res_data": {"message": "회원가입 성공"},
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
            member_type = request.data.get('type')
            pregnancy_date = request.data.get('pregnancy_date')

            profile_data = {
                "user": user.id,
                "nickname": nickname,
                "member_type": member_type,
                "pregnancy_date": pregnancy_date,
            }

            if not (nickname and member_type and pregnancy_date):
                user.delete()
                return Response({"error" : "프로필 정보를 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

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
                            "member_type": "테스트",
                            "pregnancy_date": 0,
                            },
                        "userAnalysisResult": [{"id": 1,
                                    "user_id": 2,
                                    "image": "image/url",
                                    "elapsed_time": 30,
                                    "created_at": "2024-09-26T21:10:05.460483+09:00",
                                    "IngredientResult": [
                                        {'name' : 'T1','level': 1,'notes':'부작용'},
                                        {'name' : 'T2','level': 2,'notes':'부작용'},
                                        {'name' : 'T3','level': 1,'notes':'부작용'},
                                        {'name' : 'T4','level': 1,'notes':'부작용'},
                                    ]}],
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
    def get(self, request, user_id=None):
        if user_id is None:
            user = request.user
        else:
            user = get_object_or_404(User, pk=user_id)
        profile = get_object_or_404(Profile, user=user)
        pf_serializer = ProfileSerializer(profile, context={'request':request})
        
        profile_data = pf_serializer.data
        
        data = {
            "profile": profile_data,
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
        responses=ProfileSerializer,
        request=ProfileSerializer,
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
        serializer = ProfileSerializer(profile, data=request.data)

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
        profile.name =f'deleteuser_{profile.id}'
        profile.save()
        
        user.is_active = False
        user.save()
            
        return Response({"message": "회원탈퇴 되었습니다."}, status=status.HTTP_200_OK)




