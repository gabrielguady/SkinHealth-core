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

    images_with_analysis = serializers.SerializerMethodField()

    class Meta:
        model = models.Consultation
        fields = '__all__'
        extra_kwargs = {
            'patient': {'write_only': True},
        }

    def get_patient_details(self, obj):
        return PatientSerializer(obj.patient).data

    def get_images_with_analysis(self, obj):
        file_images = obj.fileimageskin_set.all()
        results = []
        for img in file_images:
            img_data = FileImageSkinSerializer(img, context=self.context).data
            results.append(img_data)
        return results

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class FileImageSkinSerializer(serializers.ModelSerializer):
    image_url = serializers.ReadOnlyField(source='remote_name')
    analysis_result = serializers.SerializerMethodField()
    user_created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.FileImageSkin
        # Liste todos os campos que você quer incluir explicitamente
        fields = '__all__'
        extra_kwargs = {
            'filename': {'read_only': True},
            'remote_name': {'read_only': True},
            'consultation': {'write_only': True}
        }

    def get_analysis_result(self, obj):
        try:
            analysis = models.AnalysisResult.objects.get(image=obj)
            return {
                'id': analysis.id,
                'result': analysis.result,
                'confidence': analysis.confidence,
                'model_version': analysis.model_version
            }
        except models.AnalysisResult.DoesNotExist:
            return None
        except Exception as e:
            print(f"Erro ao obter analysis_result para FileImageSkin {obj.id}: {e}")
            return {"error": str(e)}


class AnalysisResultSerializer(serializers.ModelSerializer):
    user_created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.AnalysisResult
        fields = '__all__'
        extra_kwargs = {
            'image': {'write_only': True}
        }
