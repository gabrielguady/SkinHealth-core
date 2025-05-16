from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Meta:
        db_table = 'users'
        managed = True

class Patient(models.Model):
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    national_id = models.CharField(max_length=14, unique=True)

class Consultation(models.Model):
    agent = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    patient = models.ForeignKey(Patient, on_delete=models.DO_NOTHING)
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)