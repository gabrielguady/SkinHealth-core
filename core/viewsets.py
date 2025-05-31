# core/viewsets.py

from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Patient
from .serializers import PatientSerializer

from . import models, serializers
from . import serializer_params
from . import behaviors


class UserViewSet(viewsets.ModelViewSet):
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer

    def get_permissions(self):
        """
        Define as permissões para cada ação do ViewSet.
        - 'create' (registro): Permitido para qualquer usuário (não autenticado).
        - Outras ações: Requer autenticação.
        """
        if self.action in ['create', 'list']:
            return [AllowAny()]
        return [IsAuthenticated()]

    # def get_queryset(self):
    #     if self.request.user.is_authenticated:
    #         if self.request.user.is_superuser:  # Só admins podem ver todos os usuários
    #             return AuthUser.objects.all()
    #         return AuthUser.objects.filter(id=self.request.user.id)
    #     return AuthUser.objects.none()
    #
    # def perform_create(self, serializer):
    #
    #     serializer.save()


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filtra pacientes para que um usuário só possa ver/gerenciar seus próprios pacientes.
        """
        return Patient.objects.filter(user_created_by=self.request.user)

    def perform_create(self, serializer):
        """
        Associa o paciente ao usuário autenticado quando ele é criado.
        """
        serializer.save(user_created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        """
        Garante que apenas o criador ou um superusuário possa atualizar o paciente.
        """
        instance = self.get_object()
        if instance.user_created_by != request.user and not request.user.is_superuser:
            return Response(
                {"detail": "Você não tem permissão para atualizar este paciente."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Garante que apenas o criador ou um superusuário possa deletar o paciente.
        """
        instance = self.get_object()
        if instance.user_created_by != request.user and not request.user.is_superuser:
            return Response(
                {"detail": "Você não tem permissão para deletar este paciente."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


# class PatientViewSet(viewsets.ModelViewSet):
#     queryset = models.Patient.objects.all()
#     serializer_class = serializers.PatientSerializer
#     permission_classes = [AllowAny]  # Permite acesso público
#
#     def get_queryset(self):
#         user = self.request.user
#         if user.is_authenticated:
#             return models.Patient.objects.filter(user_created_by=user)
#         else:
#             return models.Patient.objects.all()  # ou .none() para esconder dados anônimos
#
#     def perform_create(self, serializer):
#         if self.request.user.is_authenticated:
#             serializer.save(user_created_by=self.request.user)
#         else:
#             serializer.save(user_created_by=None)


class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = models.Consultation.objects.all()
    serializer_class = serializers.ConsultationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filtra consultas para que um usuário só possa ver/gerenciar suas próprias consultas.
        Retorna consultas onde o usuário logado é o agente ou criador.
        """
        return models.Consultation.objects.filter(agent=self.request.user) | \
               models.Consultation.objects.filter(user_created_by=self.request.user)

    def perform_create(self, serializer):
        """
        Associa a consulta ao usuário autenticado como 'agent' e 'user_created_by'.
        """
        serializer.save(agent=self.request.user, user_created_by=self.request.user)

    @action(methods=['POST'], detail=False, parser_classes=[MultiPartParser, FormParser])
    def upload_file(self, request, *args, **kwargs):

        # Valida os parâmetros de entrada para o upload
        serializer = serializer_params.FileImageItemSerializerParam(data=request.data)
        serializer.is_valid(raise_exception=True)

        consultation_id = serializer.validated_data['consultation_id']
        image_file = serializer.validated_data['file']
        filename = serializer.validated_data.get('filename', image_file.name)

        # Garante que a consulta existe e pertence ao usuário autenticado
        consultation = get_object_or_404(
            models.Consultation,
            id=consultation_id,
            user_created_by=request.user
        )

        # Usa o comportamento para lidar com o upload e criação do FileImageSkin
        behavior_response = behaviors.MediaViewBehavior().upload_image_for_consultation(
            consultation=consultation,
            image_file=image_file,
            filename=filename,
            user=request.user
        )

        return Response(data=behavior_response, status=status.HTTP_201_CREATED)


class AnalysisResultViewSet(viewsets.ModelViewSet):
    queryset = models.AnalysisResult.objects.all()
    serializer_class = serializers.AnalysisResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filtra resultados de análise para que um usuário só possa ver/gerenciar seus próprios resultados.
        """
        return models.AnalysisResult.objects.filter(user_created_by=self.request.user)

    def perform_create(self, serializer):
        """
        Associa o resultado da análise ao usuário autenticado.
        """
        serializer.save(user_created_by=self.request.user)


class FileImageSkinViewSet(viewsets.ModelViewSet):
    queryset = models.FileImageSkin.objects.all()
    serializer_class = serializers.FileImageSkinSerializer # Usa serializers.FileImageSkinSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] # Permite leitura para não autenticados, escrita para autenticados

    def get_queryset(self):
        """
        Filtra imagens para que um usuário só possa ver/gerenciar suas próprias imagens,
        e permite filtrar por ID da consulta.
        """
        queryset = super().get_queryset()

        # Filtra por user_created_by para garantir que o usuário só veja suas próprias imagens
        if self.request.user.is_authenticated:
            queryset = queryset.filter(user_created_by=self.request.user)
        else:
            # Se não autenticado, retorna uma queryset vazia por padrão para segurança
            queryset = queryset.none()

        id_consultation = self.request.query_params.get('id_consultation')

        if id_consultation:
            # Filtra por consulta, garantindo que a consulta exista e esteja associada ao usuário (se aplicável)
            queryset = queryset.filter(consultation__id=id_consultation)

        return queryset

    def perform_create(self, serializer):
        """
        Associa a imagem ao usuário autenticado.
        """
        serializer.save(user_created_by=self.request.user)
