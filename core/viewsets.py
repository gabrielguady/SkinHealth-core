from rest_framework import viewsets

from core import models, serializers

class UserViewSet(viewsets.ModelViewSet):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer

class PatientViewSet(viewsets.ModelViewSet):
    queryset = models.Patient.objects.all()
    serializer_class = serializers.PatientSerializer

class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = models.Consultation.objects.all()
    serializer_class = serializers.ConsultationSerializer

