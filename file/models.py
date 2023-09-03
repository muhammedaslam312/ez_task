from django.db import models

from account.models import User

# Create your models here.


class File(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_content = models.FileField(upload_to="uploads/")
    upload_timestamp = models.DateTimeField(auto_now_add=True)
    file_identifier = models.CharField(
        max_length=255, unique=True
    )  # Unique identifier for the file
