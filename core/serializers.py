from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from core import models

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        data['user_name'] = self.user.username
        data['email'] = self.user.email

        return data

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.User
        fields = '__all__'
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
    user_created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.Patient
        fields = '__all__'


    def validate_gender(self, value):
        gender_mapping = {
            "Masculino": "M",
            "Feminino": "F",
            "Outro": "O"
        }
        if value in gender_mapping:
            return gender_mapping[value]
        if value in dict(models.Patient.gender.field.choices).keys():
            return value
        raise serializers.ValidationError("Gênero inválido. Use 'Masculino', 'Feminino', 'Outro', ou 'M', 'F', 'O'.")

    def validate_cpf(self, value):
        if value:
            cpf = ''.join(filter(str.isdigit, value))
            if len(cpf) != 11:
                raise serializers.ValidationError("CPF deve ter 11 dígitos.")
        return value

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret['date_of_birth']:
            ret['date_of_birth'] = instance.date_of_birth.strftime('%d/%m/%Y')
        gender_mapping = {
            "M": "Masculino",
            "F": "Feminino",
            "O": "Outro"
        }
        if ret['gender']:
            ret['gender'] = gender_mapping.get(ret['gender'], ret['gender'])
        return ret


class ConsultationSerializer(serializers.ModelSerializer):
    patient_details = PatientSerializer(source='patient', read_only=True)
    agent = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.Consultation
        fields = '__all__'

class FileImageSkinSerializer(serializers.ModelSerializer):
    image_url = serializers.ReadOnlyField(source='remote_name')

    class Meta:
        model = models.FileImageSkin
        fields = '__all__'
        extra_kwargs = {
            'filename': {'read_only': True},
            'remote_name': {'read_only': True},
            'user_created_by': {'read_only': True},
        }

    def create(self, validated_data):
        request = self.context.get('request')
        instance = models.FileImageSkin.objects.create(
            user_created_by=request.user if request and request.user.is_authenticated else None,
            **validated_data
        )
        return instance

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class AnalysisResultSerializer(serializers.ModelSerializer):
    image_details = FileImageSkinSerializer(source='image', read_only=True)
    user_created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.AnalysisResult
        fields = '__all__'
        extra_kwargs = {
            'image': {'write_only': True}
        }
