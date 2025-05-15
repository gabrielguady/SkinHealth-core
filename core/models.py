from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    full_name = models.CharField(max_length=255)
    professional_id = models.CharField(max_length=50, blank=True, null=True)

class Patient(models.Model):
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    national_id = models.CharField(max_length=14, unique=True)

class Consultation(models.Model):
    agent = models.ForeignKey(User, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

class VisualInspection(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.DO_NOTHING())
    image = models.ImageField(upload_to='inspections/')
    body_location = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)

class AnalysisResult(models.Model):
    inspection = models.OneToOneField(VisualInspection, on_delete=models.DO_NOTHING())
    classification = models.CharField(max_length=100)
    confidence = models.FloatField()
    details = models.TextField(blank=True, null=True)
    analysis_date = models.DateTimeField(auto_now_add=True)