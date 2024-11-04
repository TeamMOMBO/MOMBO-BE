from django.urls import path
from .views import IngredientAnalysis, IngredientUploadAPIView, Home

app_name = 'ingredient'

urlpatterns = [
    # path('main/', Home.as_view(), name='main'),
    path('analysis/', IngredientAnalysis.as_view(), name='ingredient'),
    path('upload/', IngredientUploadAPIView.as_view(), name='ingredient-upload'),
]