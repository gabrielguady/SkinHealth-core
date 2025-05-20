from rest_framework import serializers


class FileImageItemSerializerParam(serializers.Serializer):
    file_obj = serializers.FileField(required=True)
    consultation_id = serializers.CharField(required=False)