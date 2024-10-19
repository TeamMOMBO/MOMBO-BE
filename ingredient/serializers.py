from rest_framework import serializers
from .models import Ingredient, UserAnalysisResult, IngredientResult

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id','name', 'level', 'note']


class UserAnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnalysisResult
        fields = ['id','user_id', 'image', 'elapsed_time', 'created_at']
        

class IngredientResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngredientResult
        fields = ['id','uar_id', 'ingredient_id']