from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from core import models, serializer_params, behaviors


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = '__all__'

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = models.User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Patient
        fields = '__all__'


class ConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Consultation
        fields = '__all__'


class FileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FileImageSkin
        fields = '__all__'

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AnalysisResult
        fields = '__all__'