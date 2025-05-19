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
        self.current_time = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        self.file_extension = os.path.splitext(self.file_obj.name)[1]
        self.file_key = f'consultations/{self.consultation_id}_{self.current_time}{self.file_extension}'

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
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=self.file_key,
                Body=self.file_obj,
                ContentType=self.file_obj.content_type,
            )
            return f"{self.s3_client.meta.endpoint_url}/{self.bucket_name}/{self.file_key}"
        except Exception as e:
            raise exceptions.NotUploadMediaMinioException

    def create_image_for_consultation(self):
        if self.consultation_id or self.consultation_id.isdigit():
            consultation_id = int(self.consultation_id)
        else:
            raise ValueError(f"ID inválido: {self.consultation_id}")

        try:
            consultation = models.Consultation.objects.get(id=consultation_id)
        except models.Consultation.DoesNotExist:
            raise ValueError(f"Consulta com ID {self.consultation_id} não encontrada.")

        url = self.upload_media()
        models.FileImageSkin.objects.create(
            filename=self.file_obj.name,
            remote_name=url,
            consultation=consultation
        )

    def validate_file(self):
        if not self.file_obj.name.endswith(tuple(self.valid_extensions)):
            raise exceptions.InvalidFileException

    def run(self):
        self.validate_file()
        return self.create_image_for_consultation()