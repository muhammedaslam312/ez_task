import uuid

from django.conf import settings
from django.db import IntegrityError
from django.http import FileResponse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_yasg.utils import no_body, swagger_auto_schema
from itsdangerous import URLSafeSerializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import UserDetails
from standard.response import ErrorMessage, MessageCode, get_error_response

from .models import File

# Create your views here.


# post a file and get all file
class FileMultiView(APIView):
    permission_classes = [IsAuthenticated]

    class FileModelSerializer(serializers.ModelSerializer):
        class Meta:
            model = File
            fields = "__all__"

    class FilePostSerializer(serializers.ModelSerializer):
        class Meta:
            model = File
            fields = ["file_name", "file_content"]

        extra_kwargs = {
            "file_name": {"required": True},
            "file_content": {"required": True},
        }

    @swagger_auto_schema(
        request_body=no_body,
        responses={200: FileModelSerializer},
    )
    def get(self, *args, **kwargs):
        # Get all uploaded files
        file_objs = File.objects.all().order_by("-id")

        return Response(
            self.FileModelSerializer(file_objs, many=True).data,
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        request_body=FilePostSerializer,
        responses={201: FileModelSerializer},
    )
    def post(self, *args, **kwargs):
        serializer = self.FilePostSerializer(data=self.request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # check if the user is ops user
        user_details_obj = UserDetails.objects.get(user=self.request.user)
        if not user_details_obj.is_ops_user:
            return Response(
                get_error_response(
                    error_code=MessageCode.ACCESS_DENIED,
                    errors={"operation_user": ErrorMessage.ACCESS_DENIED_UPLOAD},
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_content = self.request.FILES.get("file_content")

        # Check the file type (only allow pptx, docx, and xlsx)
        allowed_extensions = ["pptx", "docx", "xlsx"]
        file_extension = file_content.name.split(".")[-1]
        if file_extension.lower() not in allowed_extensions:
            return Response(
                get_error_response(
                    error_code=MessageCode.INVALID_FILE_TYPE,
                    errors={"file_type": ErrorMessage.INVALID_FILE_TYPE},
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            file_obj = File.objects.create(
                user=self.request.user,
                file_name=serializer.validated_data.get("file_name"),
                file_content=file_content,
                file_identifier=str(uuid.uuid4()),
            )
        except IntegrityError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            self.FileModelSerializer(file_obj).data,
            status=status.HTTP_201_CREATED,
        )


class GenerateDownloadFileLinkView(APIView):
    permission_classes = [IsAuthenticated]

    class KwargsValidationSerializer(serializers.Serializer):
        file_id = serializers.IntegerField(required=True)

    class FileModelSerializer(serializers.ModelSerializer):
        class Meta:
            model = File
            fields = "__all__"

    @swagger_auto_schema(
        request_body=no_body,
        responses={"download_link": "", "message": "success"},
    )
    def post(self, *args, **kwargs):
        kwargs_serializer = self.KwargsValidationSerializer(data=kwargs)
        if not kwargs_serializer.is_valid():
            return Response(
                kwargs_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        file_id = kwargs_serializer.validated_data.get("file_id")

        try:
            file_obj = File.objects.get(id=file_id)
        except File.DoesNotExist:
            return Response(
                get_error_response(
                    error_code=MessageCode.INVALID_ID,
                    errors={"file_id": ErrorMessage.INVALID_ID},
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create a URL-safe serializer with a secret key (keep this secret key secure)
        serializer = URLSafeSerializer(settings.SECRET_KEY)
        signed_identifier = serializer.dumps(file_obj.file_identifier)

        domain_url = settings.CLIENT_SIDE_URL
        download_link = f"{domain_url}/api/download_file/{signed_identifier}/"

        datas = {"download_link": download_link, "message": "success"}
        return Response(datas, status=status.HTTP_200_OK)


class DownloadFileView(APIView):
    permission_classes = [IsAuthenticated]

    class KwargsValidationSerializer(serializers.Serializer):
        signed_identifier = serializers.CharField(required=True)

    def get(self, *args, **kwargs):
        kwargs_serializer = self.KwargsValidationSerializer(data=kwargs)
        if not kwargs_serializer.is_valid():
            return Response(
                kwargs_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        # check if the user is client user
        user_details_obj = UserDetails.objects.get(user=self.request.user)

        if user_details_obj.is_ops_user:
            return Response(
                get_error_response(
                    error_code=MessageCode.ACCESS_DENIED,
                    errors={"operation_user": ErrorMessage.ACCESS_DENIED_DOWNLOAD},
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        signed_identifier = kwargs_serializer.validated_data.get("signed_identifier")

        serializer = URLSafeSerializer(settings.SECRET_KEY)
        file_identifier = serializer.loads(signed_identifier)

        try:
            file_obj = File.objects.get(file_identifier=file_identifier)
        except File.DoesNotExist:
            return Response(
                get_error_response(
                    error_code=MessageCode.INVALID_ID,
                    errors={"file_id": ErrorMessage.INVALID_ID},
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_path = file_obj.file_content.path

        return FileResponse(open(file_path, "rb"))
