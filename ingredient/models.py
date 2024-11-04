from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Ingredient(models.Model):
    categoryId = models.CharField(max_length=50,null=True, blank=True)
    effectType = models.CharField(max_length=50,null=True, blank=True)
    ingredientKr = models.CharField(max_length=50,null=True, blank=True)
    ingredient = models.CharField(max_length=50,null=True, blank=True)
    level = models.CharField(max_length=50,null=True, blank=True)
    reason = models.TextField(null=True,blank=True)
    notes = models.TextField(null=True,blank=True)


class UserAnalysisResult(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.CharField(max_length=50,null=True, blank=True)
    elapsed_time = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class IngredientResult(models.Model):
    uar_id = models.ForeignKey(UserAnalysisResult, on_delete=models.CASCADE)
    ingredient_id = models.ForeignKey(Ingredient, on_delete=models.CASCADE)