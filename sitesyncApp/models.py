# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.utils import timezone
import random
import string
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    user_type = models.CharField(max_length=50, choices=[('client', 'Client'), ('contractor', 'Contractor'), ('quantity surveyor', 'Quantity Surveyor'), ('project manager', 'Project Manager'), ('architect', 'Architect'), ('engineer', 'Engineer'), ('admin', 'Administrator')])
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    used = models.BooleanField(default=False)

    def generate_otp(self):
        import random
        self.otp_code = str(random.randint(100000, 999999))
        self.created_at = timezone.now()
        self.used = False  # Reset the used flag
        self.save()

class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class BookmarkChat(models.Model):
    bookmark_id = models.AutoField(primary_key=True)
    group = models.ForeignKey('GroupChat', models.DO_NOTHING)
    chat = models.ForeignKey('Chat', models.DO_NOTHING)
    user = models.ForeignKey(User, models.DO_NOTHING)
    timestamp = models.DateTimeField()
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'bookmark_chat'
        db_table_comment = 'This Table Is Used To Store The Bookmarked Chats On the System'

class PinnedChat(models.Model):
    pinned_id = models.AutoField(primary_key=True)
    group = models.ForeignKey('GroupChat', models.DO_NOTHING)
    chat = models.ForeignKey('Chat', models.DO_NOTHING)
    user = models.ForeignKey(User, models.DO_NOTHING)
    timestamp = models.DateTimeField()
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'pinned_chat'
        db_table_comment = 'This Table Is Used To Store The Pinned Chats On the System'

class Chat(models.Model):
    chat_id = models.AutoField(primary_key=True)
    group = models.ForeignKey('GroupChat', models.DO_NOTHING)
    sender_user = models.ForeignKey(User, models.DO_NOTHING)
    message = models.TextField()
    reply = models.TextField(null=True, blank=True)
    scheduled_at = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now())
    is_deleted = models.IntegerField()
    file = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'chat'


class ChatStatus(models.Model):
    status_id = models.AutoField(primary_key=True)
    chat = models.ForeignKey(Chat, models.DO_NOTHING)
    group = models.ForeignKey('GroupChat', models.DO_NOTHING)
    user_id = models.IntegerField()
    status = models.IntegerField()
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'chat_status'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Events(models.Model):
    event_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING)
    project = models.ForeignKey('Projects', models.DO_NOTHING)
    event_name = models.CharField(max_length=75)
    event_details = models.CharField(max_length=80)
    event_date = models.DateField()
    event_start_time = models.TimeField()
    event_end_time = models.TimeField()
    event_location = models.CharField(max_length=75, blank=True, null=True)
    event_link = models.CharField(max_length=80, blank=True, null=True)
    event_status = models.CharField(max_length=9)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(blank=True, null=True)
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'events'


class GroupChat(models.Model):
    group_id = models.AutoField(primary_key=True)
    leader_id = models.IntegerField()
    project = models.OneToOneField('Projects', on_delete=models.CASCADE, related_name='groupchat')
    group_name = models.CharField(max_length=75)
    group_image = models.CharField(max_length=75, blank=True, null=True)
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'group_chat'

class ProjectMembers(models.Model):
    member_id = models.AutoField(primary_key=True)
    project = models.ForeignKey('Projects', models.DO_NOTHING)
    leader = models.ForeignKey(User, models.DO_NOTHING)
    user_name = models.CharField(max_length=75)
    status = models.CharField(max_length=75)
    user = models.ForeignKey(User, models.DO_NOTHING, related_name='projectmembers_user_set')
    created_at = models.DateTimeField()
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'project_members'


class Projects(models.Model):
    project_id = models.AutoField(primary_key=True)
    leader = models.ForeignKey(User, models.DO_NOTHING)
    project_name = models.CharField(max_length=75)
    project_details = models.CharField(max_length=255)
    project_image = models.CharField(max_length=75)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.IntegerField()
    estimated_budget = models.FloatField()
    actual_expenditure = models.FloatField()
    balance = models.FloatField()
    project_status = models.CharField(max_length=9)
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'projects'


class Resources(models.Model):
    resource_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING)
    project = models.ForeignKey(Projects, models.DO_NOTHING)
    resource_name = models.CharField(max_length=75)
    resource_details = models.CharField(max_length=80)
    resource_directory = models.CharField(max_length=75)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(blank=True, null=True)
    resource_status = models.CharField(max_length=10)
    resource_type = models.CharField(max_length=8)
    resource_size = models.CharField(max_length=8)
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'resources'


class Tasks(models.Model):
    task_id = models.AutoField(primary_key=True)
    leader = models.ForeignKey(User, models.DO_NOTHING)
    member = models.ForeignKey(User, models.DO_NOTHING, related_name='tasks_member_set')
    project = models.ForeignKey(Projects, models.DO_NOTHING)
    dependant_task_id = models.IntegerField(blank=True, null=True)
    task_name = models.CharField(max_length=75)
    task_details = models.CharField(max_length=80)
    task_given_date = models.DateField()
    task_due_date = models.DateField()
    task_completed_date = models.DateField(blank=True, null=True)
    task_days_left = models.IntegerField()
    task_days_overdue = models.IntegerField()
    task_percentage_complete = models.FloatField()
    task_status = models.CharField(max_length=15)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(blank=True, null=True)
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tasks'


class Transactions(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, models.DO_NOTHING)
    project = models.ForeignKey(Projects, models.DO_NOTHING)
    transaction_name = models.CharField(max_length=75)
    transaction_details = models.CharField(max_length=80)
    transaction_price = models.FloatField()
    transaction_quantity = models.IntegerField()
    transaction_votes_for = models.IntegerField()
    transaction_votes_against = models.IntegerField()
    total_transaction_price = models.FloatField()
    created_at = models.DateTimeField()
    transaction_date = models.CharField(max_length=15)  
    transaction_time = models.CharField(max_length=15)       
    updated_at = models.DateTimeField(blank=True, null=True)
    transaction_status = models.CharField(max_length=9)
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'transactions'


class Users(models.Model):
    user_id = models.AutoField(primary_key=True)
    fullname = models.CharField(max_length=75)
    gender = models.CharField(max_length=6)
    phone_number = models.CharField(max_length=15)
    email_address = models.CharField(unique=True, max_length=75)
    profile_picture = models.CharField(max_length=75)
    user_type = models.CharField(max_length=13)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(blank=True, null=True)
    is_deleted = models.IntegerField()
    online = models.IntegerField()
    password = models.CharField(max_length=80)

    class Meta:
        managed = False
        db_table = 'users'
