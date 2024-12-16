from django.urls import path
from .views import FAQUploadAPIView, InfomationUploadAPIView, FAQImageUpdateAPIView

app_name = 'pregnancy'

urlpatterns = [
    # path('login/', Login.as_view(), name='login'),
    path('faq/upload/', FAQUploadAPIView.as_view(), name='faq-upload'),
    path('information/upload/', InfomationUploadAPIView.as_view(), name='faq-upload'),
    path('faq/tempImg/', FAQImageUpdateAPIView.as_view(), name='faq-img-temp'),
]