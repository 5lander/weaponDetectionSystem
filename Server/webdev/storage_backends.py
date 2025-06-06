from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class PublicMediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    default_acl=None
