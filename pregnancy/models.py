from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class FAQ(models.Model):
    question = models.CharField(max_length=250,null=True, blank=True)
    real_question = models.CharField(max_length=250,null=True, blank=True)
    answer = models.CharField(max_length=250,null=True, blank=True)
    views = models.IntegerField(null=True, blank=True)


class Information(models.Model):
    step = models.CharField(max_length=50,null=True, blank=True)
    week = models.IntegerField(null=True, blank=True)
    fetus = models.CharField(max_length=50,null=True, blank=True)
    maternity = models.CharField(max_length=50,null=True, blank=True)
    summary = models.CharField(max_length=50,null=True, blank=True)

