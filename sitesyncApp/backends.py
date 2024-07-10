from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import Users

class CustomUserBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            if '@' in username:
                user = Users.objects.get(email_address=username, is_deleted=0)
            else:
                user = Users.objects.get(phone_number=username, is_deleted=0)
            
            if check_password(password, user.password):
                return user
        except Users.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Users.objects.get(pk=user_id)
        except Users.DoesNotExist:
            return None
