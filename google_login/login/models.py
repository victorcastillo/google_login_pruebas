from django.db import models

# Create your models here.
class BlackList(models.Model):
	email = models.CharField(max_length=150)