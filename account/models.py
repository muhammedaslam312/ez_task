from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class UserDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_ops_user = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
        ]
