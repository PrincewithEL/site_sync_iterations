from rest_framework import serializers
from .models import Profile

class SignInSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['user_type', 'profile_picture']
