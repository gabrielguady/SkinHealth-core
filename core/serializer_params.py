from rest_framework import serializers


class FileImageItemSerializerParam(serializers.Serializer):
    file_obj = serializers.FileField(required=True)
    id_item = serializers.CharField(required=False)