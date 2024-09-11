from rest_framework import serializers

class SignInSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField()
