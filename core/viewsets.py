
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import AuthUser

from .behaviors import MediaViewBehavior
from .models import Patient
from .serializer_params import FileImageItemSerializerParam
from .serializers import PatientSerializer

from . import models, serializers
from . import serializer_params
from . import behaviors


class UserViewSet(viewsets.ModelViewSet):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer

    def get_permissions(self):
        if self.action in ['create']:
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
        serializer.save(agent=self.request.user)

    @action(detail=False, methods=['post'], url_path='upload_file')
    def upload_file(self, request):

        serializer = FileImageItemSerializerParam(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            print(f"Erro na validação do serializer: {e}")
            print(f"Erros detalhados do serializer: {serializer.errors}")
            raise

        file_obj = serializer.validated_data['file_obj']
        consultation_id = serializer.validated_data['consultation_id']

        try:
            media_behavior = MediaViewBehavior(
                consultation_id=consultation_id,
                file_obj=file_obj,
                user_created_by=request.user
            )
            print("MediaViewBehavior instanciado. Rodando...")
            media_behavior.run()
            print("MediaViewBehavior executado com sucesso.")

            return Response(
                {'message': 'Imagem enviada e associada à consulta com sucesso!', 'consultation_id': consultation_id},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            print(f"Erro capturado no bloco try-except do viewset: {e}")
            error_message = str(e)
            if "not found" in error_message.lower():
                print("Erro: Consulta não encontrada.")
                return Response(
                    {"detail": f"Erro: {error_message}"},
                    status=status.HTTP_404_NOT_FOUND
                )
            print("Erro inesperado no MediaViewBehavior ou lógica subsequente.")
            return Response(
                {"detail": f"Erro ao processar o upload da imagem: {error_message}"},
                status=status.HTTP_400_BAD_REQUEST
            )

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

