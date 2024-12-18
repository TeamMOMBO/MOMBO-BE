from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # 쿠키에서 access_token 읽기
        access_token = request.COOKIES.get('accessToken')
        if access_token is None:
            return None

        # JWT 검증
        validated_token = self.get_validated_token(access_token)
        return self.get_user(validated_token), validated_token