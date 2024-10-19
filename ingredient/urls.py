from django.urls import path
from .views import IngredientAnalysis

app_name = 'ingredient'

urlpatterns = [
    path('analysis/', IngredientAnalysis.as_view(), name='ingredient'),
]