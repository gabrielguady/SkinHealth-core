import os

from django.contrib.sites import requests
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .behaviors import MediaViewBehavior
from .models import Patient
from .serializer_params import FileImageItemSerializerParam
from .serializers import PatientSerializer
import json
from . import models, serializers
import requests

AI_SERVICE_URL = os.environ.get('AI_SERVICE_URL', 'http://localhost:5000/predict')


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
    permission_classes = [IsAuthenticated]  # Permissão para Consultation

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
        print("--- Requisição de Upload Recebida ---")
        print(f"Método HTTP: {request.method}")
        print(f"Tipo de Conteúdo: {request.content_type}")
        print(f"Dados do Request.data (antes do serializer): {request.data}")

        serializer = FileImageItemSerializerParam(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            print(f"Dados do Serializer Validados: {serializer.validated_data}")
        except Exception as e:
            print(f"Erro na validação do serializer: {e}")
            print(f"Erros detalhados do serializer: {serializer.errors}")
            return Response(
                {"detail": "Erro na validação dos dados de upload.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        file_obj = serializer.validated_data['file_obj']
        consultation_id = serializer.validated_data['consultation_id']

        file_image_instance = None
        analysis_result_data = None

        try:
            # 1. Upload da imagem para o MinIO e criação do registro FileImageSkin
            media_behavior = MediaViewBehavior(
                consultation_id=consultation_id,
                file_obj=file_obj,
                user_created_by=request.user
            )
            # O .run() do behavior agora RETORNA a instância do FileImageSkin criada
            file_image_instance = media_behavior.run()
            print(f"FileImageSkin criado. URL: {file_image_instance.remote_name}")

            # 2. Chamar o serviço de IA (Flask) para predição
            print(f"Chamando serviço de IA em: {AI_SERVICE_URL} com imagem: {file_image_instance.remote_name}")
            try:
                ai_response = requests.post(
                    AI_SERVICE_URL,
                    json={'image_url': file_image_instance.remote_name},
                    timeout=60
                )
                ai_response.raise_for_status()

                ai_data = ai_response.json()
                if ai_data.get('status') == 'success':
                    prediction_text = ai_data.get('prediction')
                    prediction_confidence = ai_data.get('confidence')
                    model_version = ai_data.get('model_version', 'v1')

                    print(f"Predição da IA recebida: {prediction_text} (Confiança: {prediction_confidence})")

                    # 3. Criar um registro AnalysisResult no banco de dados
                    models.AnalysisResult.objects.create(
                        image=file_image_instance,
                        result=prediction_text,
                        confidence=prediction_confidence,
                        model_version=model_version
                    )
                    print("Registro AnalysisResult criado com sucesso.")

                    # Prepara os dados da análise para serem incluídos na resposta do frontend
                    analysis_result_data = {
                        "result": prediction_text,
                        "confidence": prediction_confidence,
                        "model_version": model_version
                    }
                else:
                    print(f"Serviço de IA retornou status não-sucesso: {ai_data.get('error')}")
                    analysis_result_data = {"error": ai_data.get('error', 'Erro desconhecido da IA')}

            except requests.exceptions.Timeout:
                print(f"Timeout ao chamar serviço de IA para {file_image_instance.remote_name}")
                analysis_result_data = {"error": "Timeout da IA"}
            except requests.exceptions.RequestException as e:
                print(f"Erro de requisição ao chamar serviço de IA para {file_image_instance.remote_name}: {e}")
                analysis_result_data = {"error": f"Erro de conexão com IA: {str(e)}"}
            except json.JSONDecodeError:
                print(f"Erro ao decodificar JSON da resposta da IA para {file_image_instance.remote_name}")
                analysis_result_data = {"error": "Resposta JSON inválida da IA"}
            except Exception as e:
                print(f"Erro inesperado no fluxo de IA ou DB: {e}")
                analysis_result_data = {"error": f"Erro interno ao processar IA: {str(e)}"}

            # 4. Preparar a resposta FINAL para o frontend
            # Serializa a instância do FileImageSkin (que já tem a URL da imagem)
            file_image_serializer = serializers.FileImageSkinSerializer(file_image_instance,
                                                                        context={'request': request})
            response_data = file_image_serializer.data  # Pega os dados do FileImageSkin
            response_data['analysis_result'] = analysis_result_data

            return Response(
                response_data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            print(f"Erro capturado no bloco try-except principal do viewset: {e}")
            error_message = str(e)
            if "not found" in error_message.lower():
                return Response(
                    {"detail": f"Erro: {error_message}"},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {"detail": f"Erro ao processar o upload da imagem e análise: {error_message}"},
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

