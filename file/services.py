import boto3
from django.conf import settings

from .models import File


class FilePreSignedUrlService:
    class UnsupportedTypeException(Exception):
        pass

    def __init__(
        self,
        file_obj: File,
    ):
        if file_obj.file_content is None:
            raise self.UnsupportedTypeException("UnsupportedMediaTypeException")

        file_format = file_obj.file_content.name.split(".")[-1]
        allowed_extensions = ["pptx", "docx", "xlsx"]

        if file_format.lower() not in allowed_extensions:
            raise self.UnsupportedTypeException("UnsupportedMediaTypeException")

        self.file_name = f"/media/private/uploads/f{file_obj.id}.{file_format}"

    def generate_presigned_download_url_config(self):
        s3 = boto3.client("s3")

        # Generate presigned URL for video download
        presigned_url_config = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": self.file_name},
            ExpiresIn=3600,  # URL will expire in 1 hour (3600 seconds)
        )

        return presigned_url_config
