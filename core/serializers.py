from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, Patient, Consultation, FileImageSkin, AnalysisResult
from rest_framework import serializers
from .models import Patient

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        data['user_name'] = self.user.username
        data['email'] = self.user.email

        return data

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True, 'required': True}
        }
        read_only_fields = ('id', 'date_created', 'date_modified', 'active')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
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
        model = Patient
        fields = (
            'id',
            'name',
            'date_of_birth',
            'gender',
            'cellphone',
            'cpf',
            'email',
            'user_created_by',
            'date_created',
            'date_modified',
            'active',
        )
        read_only_fields = ('id', 'user_created_by', 'date_created', 'date_modified', 'active')

    def validate_gender(self, value):
        gender_mapping = {
            "Masculino": "M",
            "Feminino": "F",
            "Outro": "O"
        }
        if value in gender_mapping:
            return gender_mapping[value]
        if value in dict(Patient.gender.field.choices).keys():
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
    images = serializers.SerializerMethodField()
    agent = serializers.PrimaryKeyRelatedField(read_only=True)
    user_created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Consultation
        fields = (
            'id',
            'agent',
            'patient',
            'patient_details',
            'date_consultation',
            'photo_location',
            'notes',
            'images',
            'user_created_by',
            'date_created',
            'date_modified',
            'active',
        )
        read_only_fields = (
            'id',
            'agent',
            'patient_details',
            'images',
            'user_created_by',
            'date_created',
            'date_modified',
            'active',
        )


    def get_images(self, obj):
        from .serializers import FileImageSkinSerializer
        images = obj.images.filter(active=True)
        return FileImageSkinSerializer(images, many=True, read_only=True, context=self.context).data


class FileImageSkinSerializer(serializers.ModelSerializer):
    image_file = serializers.FileField(write_only=True, required=False)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = FileImageSkin
        fields = (
            'id',
            'filename',
            'remote_name',
            'image_file',
            'image_url',
            'consultation',
            'user_created_by',
            'date_created',
            'date_modified',
            'active',
        )
        read_only_fields = (
            'id',
            'remote_name',
            'user_created_by',
            'date_created',
            'date_modified',
            'active',
            'image_url',
        )
        extra_kwargs = {
            'consultation': {'write_only': True}
        }

    def get_image_url(self, obj):
        if obj.image_file and obj.image_file.url:
            return obj.image_file.url
        return None

    def create(self, validated_data):
        image_file = validated_data.pop('image_file', None)
        consultation = validated_data.pop('consultation')
        request = self.context.get('request')

        file_image_skin = FileImageSkin.objects.create(
            consultation=consultation,
            user_created_by=request.user if request else None,
            **validated_data
        )

        if image_file:
            file_image_skin.image_file.save(image_file.name, image_file)
            file_image_skin.remote_name = file_image_skin.image_file.name
            file_image_skin.save()

        return file_image_skin

    def update(self, instance, validated_data):
        image_file = validated_data.pop('image_file', None)
        if image_file:
            instance.image_file.save(image_file.name, image_file)
            instance.remote_name = instance.image_file.name
        return super().update(instance, validated_data)


class AnalysisResultSerializer(serializers.ModelSerializer):
    image_details = FileImageSkinSerializer(source='image', read_only=True)
    user_created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = AnalysisResult
        fields = (
            'id',
            'image',
            'image_details',
            'result',
            'confidence',
            'model_version',
            'user_created_by',
            'date_created',
            'date_modified',
            'active',
        )
        read_only_fields = (
            'id',
            'image_details',
            'user_created_by',
            'date_created',
            'date_modified',
            'active',
        )
        extra_kwargs = {
            'image': {'write_only': True}
        }
