
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import AuthUser

from .models import Patient
from .serializers import PatientSerializer

from . import models, serializers
from . import serializer_params
from . import behaviors


class UserViewSet(viewsets.ModelViewSet):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'list']:
            return [AllowAny()]
        return [IsAuthenticated()]


    def perform_create(self, serializer):

        serializer.save()


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.filter(user_created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user_created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user_created_by != request.user and not request.user.is_superuser:
            return Response(
                {"detail": "Você não tem permissão para atualizar este paciente."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user_created_by != request.user and not request.user.is_superuser:
            return Response(
                {"detail": "Você não tem permissão para deletar este paciente."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = models.Consultation.objects.all()
    serializer_class = serializers.ConsultationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = models.Consultation.objects.filter(agent=user)

        patient_id = self.request.query_params.get('patient_id', None)
        if patient_id:
            queryset = queryset.filter(patient__id=patient_id)
        return queryset.distinct()  

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(agent=user)

    @action(methods=['POST'], detail=False, parser_classes=[MultiPartParser, FormParser])
    def upload_file(self, request, *args, **kwargs):
        serializer = serializer_params.FileImageItemSerializerParam(data=request.data)
        serializer.is_valid(raise_exception=True)

        consultation_id = serializer.validated_data['consultation_id']
        image_file = serializer.validated_data['file']
        filename = serializer.validated_data.get('filename', image_file.name)

        consultation = get_object_or_404(
            models.Consultation,
            id=consultation_id,
            user_created_by=request.user
        )

        user = request.user
        behavior_response = behaviors.MediaViewBehavior().upload_image_for_consultation(
            consultation=consultation,
            image_file=image_file,
            filename=filename,
            user=user
        )

        return Response(data=behavior_response, status=status.HTTP_201_CREATED)


class AnalysisResultViewSet(viewsets.ModelViewSet):
    queryset = models.AnalysisResult.objects.all()
    serializer_class = serializers.AnalysisResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return models.AnalysisResult.objects.filter(user_created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user_created_by=self.request.user)


class FileImageSkinViewSet(viewsets.ModelViewSet):
    queryset = models.FileImageSkin.objects.all()
    serializer_class = serializers.FileImageSkinSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_authenticated:
            queryset = queryset.filter(user_created_by=self.request.user)
        else:
            queryset = queryset.none()

        id_consultation = self.request.query_params.get('id_consultation')

        if id_consultation:
            queryset = queryset.filter(consultation__id=id_consultation)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user_created_by=self.request.user)