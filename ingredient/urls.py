from django.urls import path
from .views import IngredientAnalysis, IngredientUploadAPIView, Dictionary, AnalysisDetail

app_name = 'ingredient'

urlpatterns = [
    path('analysis/', IngredientAnalysis.as_view(), name='ingredient'),
    path('upload/', IngredientUploadAPIView.as_view(), name='ingredient-upload'),
    path('dictionary/', Dictionary.as_view(), name='ingredient-dictionary'),
    path('analysis/detil', AnalysisDetail.as_view(), name='analysis-detail'),
]