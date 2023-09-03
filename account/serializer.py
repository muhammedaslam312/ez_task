from rest_framework import serializers

from .models import User


class AccountSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "first_name",
            "last_name",
            "password1",
        )

        extra_kwargs = {
            "email": {"required": True},
            "password": {
                "write_only": True,
                "required": True,
            },
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, data):
        password1 = data.get("password")
        password = data.get("password1")

        if password and password1 and password != password1:
            raise serializers.ValidationError("Passwords do not match")
        return data


class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]
