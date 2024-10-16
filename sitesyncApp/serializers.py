from rest_framework import serializers
from .models import *

class SignInSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['user_type', 'profile_picture']

class ProfileSerializer1(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Projects
        fields = ['project_id', 'project_name', 'start_date', 'end_date', 'project_details', 'estimated_budget']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = ['task_name', 'task_status', 'project', 'start_date', 'end_date', 'task_transaction_price']

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class VerifyOtpSerializer(serializers.Serializer):
    otp_code = serializers.CharField(required=True)

class VerifyOtp1Serializer(serializers.Serializer):
    otp_code = serializers.CharField(required=True)

class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

class ProjectMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMembers
        fields = ['user_name', 'project_id', 'user_id']

class SendMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ['message', 'uid', 'file', 'scheduled_date', 'scheduled_time', 'reply_message_id', 'selected_users']

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resources
        fields = [
            'resource_id', 'resource_name', 'resource_details', 
            'resource_type', 'is_deleted', 'created_at', 'updated_at'
        ]

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transactions
        fields = '__all__'

class EventsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = '__all__'

class ChatStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatStatus
        fields = ['status', 'timestamp', 'user_id']
