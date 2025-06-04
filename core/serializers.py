from rest_framework import serializers
from core import models

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ['id', 'username', 'email', 'professional_id', 'password']
        extra_kwargs = {
            'password': {'write_only': True, 'required': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = models.User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        return super().update(instance, validated_data)


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Patient
        fields = '__all__'
        read_only_fields = ['id', 'date_created', 'date_modified', 'active']


class FileImageSerializer(serializers.ModelSerializer): # Mantendo o nome FileImageSerializer
    image_file = serializers.ImageField(use_url=True, required=True)

    class Meta:
        model = models.FileImageSkin # O serializer é para o modelo FileImageSkin
        fields = ['id', 'filename', 'image_file', 'consultation', 'date_created', 'date_modified', 'active']
        read_only_fields = ['id', 'date_created', 'date_modified', 'active', 'consultation']


class ResultSerializer(serializers.ModelSerializer): # Mantendo o nome ResultSerializer
    image_url = serializers.SerializerMethodField()
    image_id = serializers.PrimaryKeyRelatedField(
        queryset=models.FileImageSkin.objects.all(),
        source='image',
        write_only=True
    )

    class Meta:
        model = models.AnalysisResult # O serializer é para o modelo AnalysisResult
        fields = ['id', 'image_id', 'image_url', 'result', 'confidence', 'model_version', 'date_created', 'date_modified', 'active']
        read_only_fields = ['id', 'date_created', 'date_modified', 'active', 'image_url']

    def get_image_url(self, obj):
        if obj.image and obj.image.image_file:
            return obj.image.image_file.url
        return None


class ConsultationSerializer(serializers.ModelSerializer):
    agent_id = serializers.PrimaryKeyRelatedField(
        queryset=models.User.objects.all(),
        source='agent',
        write_only=True,
        required=False
    )
    agent_username = serializers.CharField(source='agent.username', read_only=True)

    patient_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Patient.objects.all(),
        source='patient',
        write_only=True
    )
    patient_name = serializers.CharField(source='patient.name', read_only=True)

    # Use o nome do serializer existente: FileImageSerializer
    images = FileImageSerializer(many=True, read_only=True, source='images') # source='images' corresponde ao related_name

    # Para ver resultados de todas as imagens da consulta. Ajustado para o related_name padrão ou explícito.
    # Se em FileImageSkin o ForeignKey para Consultation não tem related_name, o padrão é 'fileimageskin_set'.
    # E se em AnalysisResult o ForeignKey para FileImageSkin não tem related_name, o padrão é 'analysisresult_set'.
    # Então, para acessar os resultados via consulta->imagem->resultado:
    analysis_results_for_images = serializers.SerializerMethodField()

    class Meta:
        model = models.Consultation
        fields = [
            'id', 'agent_id', 'agent_username', 'patient_id', 'patient_name',
            'date_consultation', 'photo_location', 'notes',
            'ai_diagnosis', 'ai_confidence', # Campos que podem ser atualizados pela IA (assumindo que existam no modelo Consultation)
            'images', 'analysis_results_for_images', # Inclua as imagens e resultados
            'date_created', 'date_modified', 'active'
        ]
        read_only_fields = [
            'id', 'agent_username', 'patient_name', 'images', 'analysis_results_for_images',
            'date_created', 'date_modified', 'active'
        ]

    def get_analysis_results_for_images(self, obj):
        # Percorre as imagens da consulta e coleta seus resultados
        results = []
        # 'images' aqui é o related_name do ForeignKey em FileImageSkin para Consultation
        for image_obj in obj.images.all(): # Assumindo related_name='images' no FileImageSkin
            # 'analysisresult_set' é o related_name padrão do ForeignKey em AnalysisResult para FileImageSkin
            for result_obj in image_obj.analysisresult_set.all():
                results.append(ResultSerializer(result_obj).data) # Usa o ResultSerializer existente
        return results

    def create(self, validated_data):
        request = self.context.get('request')
        if 'agent' not in validated_data and request and request.user.is_authenticated:
            validated_data['agent'] = request.user
        elif 'agent' not in validated_data:
            raise serializers.ValidationError({"agent_id": "O ID do agente é obrigatório."})
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)