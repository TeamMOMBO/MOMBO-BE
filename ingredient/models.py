from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(null=True, blank=True)
    level = models.IntegerField(null=True, blank=True)
    note = models.TextField(null=True,blank=True)


class UserAnalysisResult(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.CharField(null=True, blank=True)
    elapsed_time = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class IngredientResult(models.Model):
    uar_id = models.ForeignKey(UserAnalysisResult, on_delete=models.CASCADE)
    ingredient_id = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
