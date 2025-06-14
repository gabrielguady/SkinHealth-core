import os
from abc import ABC, abstractmethod
from datetime import datetime

import boto3
from botocore.config import Config
from core import exceptions, models


class BaseBehavior(ABC):
    @abstractmethod
    def run(self):
        raise NotImplementedError('You must subclass and implement the trace rule validation')


class MediaViewBehavior(BaseBehavior):

    def __init__(self, **kwargs):
        self.valid_extensions = ['.jpeg', '.jpg', '.png']
        self.s3_client = self.s3_client_init()
        self.bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME')
        self.consultation_id = kwargs.get('consultation_id')
        self.file_obj = kwargs.get('file_obj')

        self.user_created_by = kwargs.get('user_created_by', None)

        self.current_time = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        self.file_extension = os.path.splitext(self.file_obj.name)[1]
        self.file_key = f'consultation/{self.consultation_id}_{self.current_time}_{os.urandom(4).hex()}{self.file_extension}'

        print(
            f"Behavior Init: consultation_id={self.consultation_id}, file_obj={self.file_obj.name if self.file_obj else 'NULO'}, user_created_by={self.user_created_by if hasattr(self, 'user_created_by') else 'NÃO PASSADO/DEFINIDO'}")

    @staticmethod
    def s3_client_init():
        return boto3.client('s3',
                            endpoint_url=os.environ.get('AWS_S3_ENDPOINT_URL'),
                            aws_access_key_id=os.environ.get('AWS_S3_ACCESS_KEY_ID'),
                            aws_secret_access_key=os.environ.get('AWS_S3_SECRET_ACCESS_KEY'),
                            config=Config(signature_version='s3v4'),
                            region_name='sa-east-1',
                            verify=False)

    def upload_media(self):
        print(
            f"Iniciando upload para MinIO. Bucket: {self.bucket_name}, Key: {self.file_key}, Content-Type: {self.file_obj.content_type}")
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self.file_key,
                Body=self.file_obj,
                ContentType=self.file_obj.content_type,
            )
            return f"{self.s3_client.meta.endpoint_url}/{self.bucket_name}/{self.file_key}"
        except Exception as e:
            raise exceptions.NotUploadMediaMinioException(f"Erro ao fazer upload para o Minio: {e}")

    def create_image_for_consultation(self):
        if self.consultation_id is None or not str(self.consultation_id).isdigit():
            raise ValueError(f"ID inválido: {self.consultation_id}")

        consultation_id = int(self.consultation_id)

        try:
            consultation = models.Consultation.objects.get(id=consultation_id)
            print(f"Consulta ID {consultation_id} encontrada: {consultation.date_consultation}")
        except models.Consultation.DoesNotExist:
            print(f"Erro: Consulta com ID {self.consultation_id} NÃO encontrada.")
            raise ValueError(f"Consulta com ID {self.consultation_id} não encontrada.")

        url = self.upload_media()

        print(
            f"Tentando criar objeto FileImageSkin: filename={self.file_obj.name}, remote_name={url}, consultation={consultation.id}")
        models.FileImageSkin.objects.create(
            filename=self.file_obj.name,
            remote_name=url,
            consultation=consultation,
        )
        print("Registro FileImageSkin criado com sucesso.")

    def validate_file(self):
        print(f"Validando arquivo: {self.file_obj.name}, tamanho: {self.file_obj.size}")
        if not self.file_obj.name.lower().endswith(tuple(self.valid_extensions)):
            print("Validação de arquivo FALHOU: Extensão inválida.")
            raise exceptions.InvalidFileException(
                "Formato de arquivo inválido. Apenas .jpeg, .jpg, .png são permitidos.")
        print("Validação de arquivo OK.")

    def run(self):
        print("MediaViewBehavior.run() iniciado.")
        self.validate_file()
        self.create_image_for_consultation()
        print("MediaViewBehavior.run() concluído.")