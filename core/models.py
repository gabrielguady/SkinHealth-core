from django.contrib.auth.models import AbstractUser
from django.db import models


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
        null=False,
    )
    gender = models.CharField(
        db_column='tx_gender',
        max_length=10,
        choices=[('M', 'Male'),
                 ('F', 'Female'),
                 ('O', 'Other')]
    )
    cellphone = models.IntegerField(
        db_column='nb_cellphone',
        null=True,
    )
    cpf = models.CharField(
        db_column='tx_national_id',
        max_length=14,
        unique=True
    )
    email = models.EmailField(
        db_column='tx_email',
    )


class Consultation(ModelBase):
    agent = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column='id_agent',
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.DO_NOTHING,
        db_column='id_patient',
    )
    date_consultation = models.DateTimeField(
        db_column='dt_date_consultation',
    )
    photo_location = models.CharField(
        db_column='tx_photo_location',
        max_length=255,
    )
    notes = models.TextField(
        db_column='tx_notes',
        blank=True,
        null=True
    )


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
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.DO_NOTHING,
        db_column='id_consultation',
    )

    class Meta:
        db_table = 'file_image_item'
        managed = True

class AnalysisResult(ModelBase):
    image = models.ForeignKey(
        FileImageSkin,
        on_delete=models.DO_NOTHING,
        db_column='id_image',
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
    class Meta:
        db_table = 'analysis_result'
        managed = True
