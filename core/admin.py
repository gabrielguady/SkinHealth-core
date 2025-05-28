from django.contrib import admin
from .models import Patient, Consultation, FileImageSkin, User, AnalysisResult

admin.site.register(Patient)
admin.site.register(Consultation)
admin.site.register(FileImageSkin)
admin.site.register(User)
admin.site.register(AnalysisResult)
