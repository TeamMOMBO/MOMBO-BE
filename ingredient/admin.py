from django.contrib import admin
from .models import Ingredient, UserAnalysisResult, IngredientResult

# Register your models here.
admin.site.register(Ingredient)
admin.site.register(UserAnalysisResult)
admin.site.register(IngredientResult)