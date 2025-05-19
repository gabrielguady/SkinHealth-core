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

    @action(methods=['POST'], detail=False, parser_classes=[MultiPartParser])
    def upload_file(self, request, *args, **kwargs):
        serializer = serializer_params.FileImageItemSerializerParam(data=request.data)
        serializer.is_valid(raise_exception=True)

        behavior = behaviors.MediaViewBehavior(**serializer.validated_data)
        response = behavior.run()

        return Response(data=response, status=status.HTTP_201_CREATED)


class FileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FileImageSkin
        fields = '__all__'

class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AnalysisResult
        fields = '__all__'