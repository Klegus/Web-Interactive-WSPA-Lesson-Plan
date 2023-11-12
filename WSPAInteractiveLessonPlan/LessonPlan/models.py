from django.db import models

# Create your models here.
class INFST1(models.Model):
    group1 = models.JSONField()
    group2 = models.JSONField()
    group3 = models.JSONField()
    group4 = models.JSONField()
    group5 = models.JSONField()
    group6 = models.JSONField()
    update_time = models.DateTimeField(auto_now=True)
    update_speed = models.IntegerField(default=0)
    checksum = models.CharField(max_length=64, default="")