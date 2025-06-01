from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid
from .validators import custom_username_validator

class ModelBase(models.Model):
    id = models.BigAutoField(
        primary_key=True,
        null=False,
        db_column='id',
    )
    date_created = models.DateTimeField(
        db_column='dt_created',
        auto_now_add=True,
        null=False,
    )
    date_modified = models.DateTimeField(
        db_column='dt_modified',
        auto_now=True,
        null=False,
    )
    active = models.BooleanField(
        db_column='cs_active',
        default=True,
    )

    class Meta:
        abstract = True
        managed = True


class User(AbstractUser):
    # SOBRESCREVER O CAMPO USERNAME PARA REMOVER/SUBSTITUIR OS VALIDORES PADRÃO
    # O AbstractUser define username com max_length=150. É bom manter isso.
    # username = models.CharField(
    #     db_column='tx_username',
    #     max_length=150,
    #     unique=True,
    #     help_text=('Obrigatório. 150 caracteres ou menos. Letras, números, @/./+/-/_ e espaços.'),
    #     error_messages={
    #         'unique': ("Já existe um usuário com este nome de usuário."),
    #     },
    #     validators=[custom_username_validator],
    # )

    professional_id = models.CharField(
        db_column='tx_professional_id',
        null=False,
        blank=False,
        unique=True,
        max_length=255,
    )
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class Patient(ModelBase):
    name = models.CharField(
        db_column='tx_name',
        max_length=255,
        null=False,
    )
    date_of_birth = models.DateField(
        db_column='dt_date_of_birth',
        null=True,
        blank=True,
    )
    gender = models.CharField(
        db_column='tx_gender',
        max_length=10,
        choices=[('M', 'Male'),
                 ('F', 'Female'),
                 ('O', 'Other')],
        blank=True,
        null=True,
    )
    cellphone = models.CharField(
        db_column='nb_cellphone',
        max_length=30,
        null=True,
        blank=True,
    )
    cpf = models.CharField(
        db_column='tx_national_id',
        max_length=14,
        unique=True,
        blank=True,
        null=True,
    )
    email = models.EmailField(
        db_column='tx_email',
        blank=True,
        null=True,
    )
    user_created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='patients')

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'


class Consultation(ModelBase):
    agent = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column='id_agent',
        related_name='consultations_as_agent',
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        db_column='id_patient',
        related_name='consultations',
    )
    date_consultation = models.DateTimeField(
        db_column='dt_date_consultation',
        default=timezone.now,
    )
    photo_location = models.CharField(
        db_column='tx_photo_location',
        max_length=255,
        blank=True,
        null=True,
    )
    notes = models.TextField(
        db_column='tx_notes',
        blank=True,
        null=True
    )
    user_created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_consultations')

    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'


class FileImageSkin(ModelBase):
    filename = models.CharField(
        db_column='tx_file_name',
        null=False,
        blank=False,
        max_length=255,
    )
    remote_name = models.CharField(
        db_column='tx_remote_name',
        max_length=1024,
        null=False,
        blank=False,
    )
    image_file = models.ImageField(
        db_column='im_image_file',
        upload_to='analysis_images/',
        null=True,
        blank=True,
    )
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.DO_NOTHING,
        db_column='id_consultation',
        related_name='images',
    )
    user_created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_images')

    class Meta:
        db_table = 'file_image_item'
        managed = True
        verbose_name = 'Imagem de Pele'
        verbose_name_plural = 'Imagens de Pele'


class AnalysisResult(ModelBase):
    image = models.ForeignKey(
        FileImageSkin,
        on_delete=models.DO_NOTHING,
        db_column='id_image',
        related_name='analysis_results',
    )
    result = models.CharField(
        db_column='tx_result',
        max_length=255
    )
    confidence = models.FloatField()
    model_version = models.CharField(
        db_column='tx_model_version',
        max_length=20,
        default='v1'
    )
    user_created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_analysis_results')

    class Meta:
        db_table = 'analysis_result'
        managed = True
        verbose_name = 'Resultado de Análise'
        verbose_name_plural = 'Resultados de Análise'