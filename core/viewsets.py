from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
import core.models as models

from core.serializers import (
    UserSerializer,
    PatientSerializer,
    ConsultationSerializer,
    FileImageSerializer,
    ResultSerializer
)

class UserViewSet(viewsets.ModelViewSet):
    queryset = models.User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['create']:
            return [AllowAny()]
        return [IsAuthenticated()]

class PatientViewSet(viewsets.ModelViewSet):
    queryset = models.Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = models.Consultation.objects.all()
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Garante que o usuário só possa ver as consultas dos seus próprios pacientes
        patient_pk = self.kwargs.get('patient_pk') # Se a URL é aninhada
        if patient_pk:
            return models.Consultation.objects.filter(
                patient_id=patient_pk,
                patient__user=self.request.user
            )
        return models.Consultation.objects.filter(patient__user=self.request.user)


    def perform_create(self, serializer):
        patient_pk = self.kwargs.get('patient_pk')
        if not patient_pk:
            raise serializers.ValidationError({"patient_id": "ID do paciente é necessário na URL para criar a consulta."})

        try:
            patient = models.Patient.objects.get(id=patient_pk, user=self.request.user)
        except models.Patient.DoesNotExist:
            raise serializers.ValidationError({"patient_id": "Paciente não encontrado ou não pertence ao usuário logado."})

        serializer.save(patient=patient, agent=self.request.user) # Associa o agente e o paciente à consulta

class ResultViewSet(viewsets.ModelViewSet): # Mantido o nome ResultViewSet
    queryset = models.AnalysisResult.objects.all()
    serializer_class = ResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Garante que o usuário só possa ver os resultados de suas próprias imagens/consultas
        fileimageskin_pk = self.kwargs.get('fileimageskin_pk') # Se a URL é aninhada
        if fileimageskin_pk:
            return self.queryset.filter(
                image_id=fileimageskin_pk,
                image__consultation__patient__user=self.request.user
            )
        return self.queryset.filter(image__consultation__patient__user=self.request.user) # Para listar todos os resultados do usuário


class FileImageViewSet(viewsets.ModelViewSet):
    queryset = models.FileImageSkin.objects.all()
    serializer_class = FileImageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        consultation_pk = self.kwargs.get('consultation_pk')
        if consultation_pk:
            return self.queryset.filter(
                consultation_id=consultation_pk,
                consultation__patient__user=self.request.user
            )
        return self.queryset.filter(consultation__patient__user=self.request.user)

    def perform_create(self, serializer):
        consultation_pk = self.kwargs.get('consultation_pk')
        if not consultation_pk:
            raise serializers.ValidationError({"detail": "ID da consulta é necessário para fazer upload da imagem."})

        try:
            consultation = models.Consultation.objects.get(
                id=consultation_pk,
                patient__user=self.request.user
            )
        except models.Consultation.DoesNotExist:
            raise serializers.ValidationError({"detail": "Consulta não encontrada ou não pertence ao usuário."})

        file_image_skin = serializer.save(consultation=consultation)

        # TODO: Chamar a IA aqui com o 'file_image_skin.image_file.url'
        ai_result_text = "Resultado da IA: Benigno"
        ai_confidence_score = 0.95

        models.AnalysisResult.objects.create(
            image=file_image_skin,
            result=ai_result_text,
            confidence=ai_confidence_score,
            model_version='v1.0'
        )

        consultation.ai_diagnosis = ai_result_text
        consultation.ai_confidence = ai_confidence_score
        consultation.save()