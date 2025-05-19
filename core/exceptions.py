from rest_framework.exceptions import APIException


class NotUploadMediaMinioException(APIException):
    status_code = 400
    default_detail = 'Erro em subir midia para o minio'

class InvalidFileException(APIException):
    status_code = 400
    default_detail = 'Tipo de arquivo inválido'