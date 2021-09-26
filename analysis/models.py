from typing import DefaultDict
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Playstyle(models.Model):
    champion = models.TextField(max_length=20)
    date_reviewed=models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.champion