from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from account.jwt import CustomTokenObtainPairSerializer
from file.models import File

from .models import UserDetails

User = get_user_model()


class TestSetUp(APITestCase):
    def setUp(self):
        self.ops_user_data = {
            "email": "opsuser@gmail.com",
            "first_name": "ops_user",
            "last_name": "m",
            "password": "12345",
        }
        self.client_user_data = {
            "email": "clientuser@gmail.com",
            "first_name": "client_user",
            "last_name": "m",
            "password": "12345",
        }

        self.ops_user_obj = User.objects.create(
            email=self.ops_user_data["email"],
            username=self.ops_user_data["email"],  # Must be Same as Email
            first_name=self.ops_user_data["first_name"],
            last_name=self.ops_user_data["last_name"],
            is_active=True,
        )
        self.ops_user_details_obj = UserDetails.objects.create(
            user=self.ops_user_obj,
            is_ops_user=True,
        )
        self.ops_user_obj.set_password(self.ops_user_data["password"])
        self.ops_user_obj.save()

        self.client_user_obj = User.objects.create(
            email=self.client_user_data["email"],
            username=self.client_user_data["email"],  # Must be Same as Email
            first_name=self.client_user_data["first_name"],
            last_name=self.client_user_data["last_name"],
            is_active=True,
        )
        self.client_user_details_obj = UserDetails.objects.create(
            user=self.client_user_obj,
            is_ops_user=False,
        )
        self.client_user_obj.set_password(self.client_user_data["password"])
        self.client_user_obj.save()

        ops_refresh = CustomTokenObtainPairSerializer.get_token(self.ops_user_obj)
        self.ops_token = str(ops_refresh.access_token)

        client_refresh = CustomTokenObtainPairSerializer.get_token(self.client_user_obj)
        self.clinet_token = str(client_refresh.access_token)

        # Create a sample file to use in the test
        self.uploaded_file = SimpleUploadedFile("test_file.pptx", b"file_content")
        self.uploaded_file1 = SimpleUploadedFile("test_file.ppt", b"file_content")

        return super().setUp()


class TestViews(TestSetUp):
    def test_ops_user_signup_view(self):
        url = reverse("ops_user_register_view")
        # register valid data
        data = {
            "email": "ops@register.com",
            "password": "12345",
            "password1": "12345",
            "first_name": "first_name",
            "last_name": "last_name",
        }
        response = self.client.post(url, data=data, format="json")
        # import pdb
        # pdb.set_trace()
        self.assertEqual(response.status_code, 201)

        user = User.objects.latest("id")
        self.assertEqual(user.email, data["email"])
        self.assertEqual(user.first_name, data["first_name"])
        self.assertEqual(user.last_name, data["last_name"])

    def test_login_view(self):
        login_url = reverse("user_login_view")
        # ops_user_login
        data = {
            "username": self.ops_user_data["email"],
            "password": self.ops_user_data["password"],
        }
        response = self.client.post(login_url, data=data, format="json")
        self.assertEqual(response.status_code, 200)

        # Logout
        self.client.logout()

        # client_user_login
        data = {
            "username": self.client_user_data["email"],
            "password": self.client_user_data["password"],
        }
        response = self.client.post(login_url, data=data, format="json")
        self.assertEqual(response.status_code, 200)

    def test_file_post_view(self):
        file_post_view_url = reverse("file_multi_view")

        # post file using ops_user token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.ops_token}")

        # POST with valid file(pptx,docx, and xlsx) data
        data = {
            "file_name": "test_file",
            "file_content": self.uploaded_file,
        }
        response = self.client.post(file_post_view_url, data=data, format="json")
        # import pdb
        # pdb.set_trace()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # POST with out valid file(pptx,docx, and xlsx) data
        data = {
            "file_name": "test file",
            "file_content": self.uploaded_file1,
        }
        response = self.client.post(file_post_view_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # test by using client_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.clinet_token}")

        # POST with valid file(pptx,docx, and xlsx) data
        data = {
            "file_name": "test_file",
            "file_content": self.uploaded_file,
        }
        response = self.client.post(file_post_view_url, data=data, format="json")
        # import pdb
        # pdb.set_trace()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
