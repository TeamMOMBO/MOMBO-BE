from django.urls import path
from .views import IngredientAnalysis, IngredientUploadAPIView

app_name = 'ingredient'

urlpatterns = [
    path('analysis/', IngredientAnalysis.as_view(), name='ingredient'),
    path('upload/', IngredientUploadAPIView.as_view(), name='ingredient-upload'),
]