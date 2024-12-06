from django.urls import path
from .views import IngredientAnalysis, IngredientUploadAPIView, Dictionary

app_name = 'ingredient'

urlpatterns = [
    path('analysis/', IngredientAnalysis.as_view(), name='ingredient'),
    path('upload/', IngredientUploadAPIView.as_view(), name='ingredient-upload'),
    path('dictionary/', Dictionary.as_view(), name='ingredient-dictionary'),
]