from rest_framework import serializers
from .models import *

class SignInSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['user_type', 'profile_picture']

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Projects
        fields = ['project_id', 'project_name', 'start_date', 'end_date', 'leader_id', 'project_status']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = ['task_name', 'task_status', 'project', 'start_date', 'end_date']
