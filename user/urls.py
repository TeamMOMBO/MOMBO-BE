from django.urls import path
from .views import Login, Join, Withdrawal, Logout, KakaoLogin, ProfileView, ProfileEditView
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import views as auth_views

app_name = 'user'

urlpatterns = [
    path('login/', Login.as_view(), name='login'),
    path('join/', Join.as_view(), name='join'),
    path("logout/", Logout.as_view(), name='logout'),
    path("withdrawal/", Withdrawal.as_view(), name='withdrawal'),
    path("login/kakao/callback/", KakaoLogin.as_view(), name='kakao-callback'),
    path("profile/", ProfileView.as_view(), name='profile'),
    path("profile/edit/", ProfileEditView.as_view(), name='profile-edit'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]