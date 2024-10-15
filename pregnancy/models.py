from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class FAQ(models.Model):
    question = models.CharField(null=True, blank=True)
    real_question = models.CharField(null=True, blank=True)
    answer = models.CharField(null=True, blank=True)
    views = models.IntegerField(null=True, blank=True)


class Information(models.Model):
    step = models.CharField(null=True, blank=True)
    Week = models.IntegerField(null=True, blank=True)
    fetus = models.CharField(null=True, blank=True)
    maternity = models.CharField(null=True, blank=True)
    summary = models.CharField(null=True, blank=True)

