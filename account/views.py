from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from drf_yasg.utils import no_body, swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from standard.response import ErrorMessage, MessageCode, get_error_response

from .jwt import CustomTokenObtainPairSerializer
from .models import User, UserDetails
from .serializer import AccountSerializer, UserModelSerializer

# Create your views here.


class OpsUserSignupView(APIView):
    serializer_class = AccountSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=AccountSerializer,
        responses={
            201: UserModelSerializer,
        },
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                user_obj = User.objects.create(
                    email=serializer.validated_data["email"],
                    username=serializer.validated_data[
                        "email"
                    ],  # Must be Same as Email
                    first_name=serializer.validated_data["first_name"],
                    last_name=serializer.validated_data["last_name"],
                    is_active=True,  # ops user not need verification
                )
                password = serializer.validated_data["password"]
                user_obj.set_password(password)
                user_obj.save()

                # create user_details using
                UserDetails.objects.create(
                    user=user_obj,
                    is_ops_user=True,
                )

        except IntegrityError:
            return Response(
                get_error_response(
                    error_code=MessageCode.UNIQUE_CONSTRAINT,
                    errors={"email": ErrorMessage.UNIQUE_CONSTRAINT},
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            UserModelSerializer(user_obj).data, status=status.HTTP_201_CREATED
        )


class ClientUserSignupView(APIView):
    serializer_class = AccountSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=AccountSerializer,
        responses={
            201: UserModelSerializer,
        },
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        try:
            user_obj = User.objects.get(email=email)

        except User.DoesNotExist:
            with transaction.atomic():
                user_obj = User.objects.create(
                    email=email,
                    username=serializer.validated_data[
                        "email"
                    ],  # Must be Same as Email
                    first_name=serializer.validated_data["first_name"],
                    last_name=serializer.validated_data["last_name"],
                    is_active=False,  # client user need verification
                )
                password = serializer.validated_data["password"]
                user_obj.set_password(password)
                user_obj.save()

                # create user_details using
                UserDetails.objects.create(
                    user=user_obj,
                    is_ops_user=False,
                )

        # resent activation link logic
        if user_obj.is_active:
            return Response(
                get_error_response(
                    error_code=MessageCode.EMAIL_ALREADY_VERIFIED,
                    errors={"error": ErrorMessage.EMAIL_ALREADY_VERIFIED},
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        to_emails = user_obj.email
        uidb64 = urlsafe_base64_encode(force_bytes(user_obj.pk))
        verification_token = default_token_generator.make_token(user_obj)

        domain_url = settings.CLIENT_SIDE_URL
        verify_url = f"{domain_url}/api/verify/{uidb64}/{verification_token}/"

        subject = "Email Verification"
        message = f"Click the following link to verify your email: {verify_url}"
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [to_emails]  # User's email address

        send_mail(subject, message, from_email, recipient_list)

        return Response(
            UserModelSerializer(user_obj).data, status=status.HTTP_201_CREATED
        )


class UserLoginView(APIView):
    serializer_class = AuthTokenSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=AuthTokenSerializer,
        responses={
            200: None,
        },
    )
    def post(self, request, format=None):
        serializer = self.serializer_class(
            context={"request": request}, data=request.data
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]
        # Here you are logging in the user
        login(request, user)
        # Creating a JWT token
        refresh = CustomTokenObtainPairSerializer.get_token(user)

        # Returning the token and the expiry
        return Response(
            {"token": str(refresh.access_token)},
            status=status.HTTP_200_OK,
        )


# direct activate from email
def email_activate(request, uidb64, verification_token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(
        user, verification_token
    ):
        user.is_active = True
        user.save()
        return HttpResponse("Your account has been successfully activated.")
    else:
        return HttpResponse("Activation failed try again..!")
