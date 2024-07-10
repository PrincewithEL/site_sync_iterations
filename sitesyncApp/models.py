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
    user_type = models.CharField(max_length=50, choices=[('client', 'Client'), ('contractor', 'Contractor'), ('admin', 'Administrator')])
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now=True)
    used = models.BooleanField(default=False)

    def generate_otp(self):
        import random
        self.otp_code = str(random.randint(100000, 999999))
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
    bookmark_id = models.AutoField(db_column='Bookmark_ID', primary_key=True)  # Field name made lowercase.
    group = models.ForeignKey('GroupChat', models.DO_NOTHING, db_column='Group_ID')  # Field name made lowercase.
    chat = models.ForeignKey('Chat', models.DO_NOTHING, db_column='Chat_ID')  # Field name made lowercase.
    user = models.ForeignKey('Users', models.DO_NOTHING, db_column='User_ID')  # Field name made lowercase.
    timestamp = models.DateTimeField(db_column='Timestamp')  # Field name made lowercase.
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'bookmark_chat'
        db_table_comment = 'This Table Is Used To Store The Bookmarked Chats On the System'


class Chat(models.Model):
    chat_id = models.AutoField(db_column='Chat_ID', primary_key=True)  # Field name made lowercase.
    group = models.ForeignKey('GroupChat', models.DO_NOTHING, db_column='Group_ID')  # Field name made lowercase.
    sender_user = models.ForeignKey(User, models.DO_NOTHING, db_column='Sender_User_ID')  # Field name made lowercase.
    message = models.TextField(db_column='Message')  # Field name made lowercase.
    timestamp = models.DateTimeField(db_column='Timestamp', default=timezone.now)  # Field name made lowercase.
    is_deleted = models.IntegerField()
    file = models.TextField(db_column='File',null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'chat'
        db_table_comment = 'This Table Is Used To Store The Chat Details On the System'


class ChatStatus(models.Model):
    status_id = models.AutoField(db_column='Status_ID', primary_key=True)  # Field name made lowercase.
    chat = models.ForeignKey(Chat, models.DO_NOTHING, db_column='Chat_ID')  # Field name made lowercase.
    group = models.ForeignKey('GroupChat', models.DO_NOTHING, db_column='Group_ID')  # Field name made lowercase.
    user_id = models.IntegerField(db_column='User_ID')  # Field name made lowercase.
    status = models.IntegerField(db_column='Status')  # Field name made lowercase.
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'chat_status'
        db_table_comment = 'This Table Is Used To Store The Chat Status Details On the System'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
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
    event_id = models.AutoField(db_column='Event_ID', primary_key=True)  # Field name made lowercase.
    user = models.ForeignKey(User, models.DO_NOTHING, db_column='User_ID')  # Field name made lowercase.
    project = models.ForeignKey('Projects', models.DO_NOTHING, db_column='Project_ID')  # Field name made lowercase.
    event_name = models.CharField(db_column='Event_Name', max_length=75)  # Field name made lowercase.
    event_details = models.CharField(db_column='Event_Details', max_length=80)  # Field name made lowercase.
    event_date = models.DateField(db_column='Event_Date')  # Field name made lowercase.
    event_start_time = models.TimeField(db_column='Event_Start_Time')  # Field name made lowercase.
    event_end_time = models.TimeField(db_column='Event_End_Time')  # Field name made lowercase.
    event_location = models.CharField(db_column='Event_Location', max_length=75, blank=True, null=True)  # Field name made lowercase.
    event_link = models.CharField(db_column='Event_Link', max_length=80, blank=True, null=True)  # Field name made lowercase.
    event_status = models.CharField(db_column='Event_Status', max_length=9)  # Field name made lowercase.
    created_at = models.DateTimeField(db_column='Created_At')  # Field name made lowercase.
    updated_at = models.DateTimeField(db_column='Updated_At', blank=True, null=True)  # Field name made lowercase.
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'events'
        db_table_comment = 'This Table Is Used To Store Event Details On the System'

class GroupChat(models.Model):
    group_id = models.AutoField(db_column='Group_ID', primary_key=True)  # Field name made lowercase.
    leader_id = models.IntegerField(db_column='Leader_ID')  # Field name made lowercase.
    # project = models.ForeignKey('Projects', models.DO_NOTHING, db_column='Project_ID')  # Field name made lowercase.
    project = models.OneToOneField('Projects', on_delete=models.CASCADE, related_name='groupchat')
    group_name = models.CharField(db_column='Group_Name', max_length=75)  # Field name made lowercase.
    group_image = models.CharField(db_column='Group_Image', max_length=75, blank=True, null=True)  # Field name made lowercase.
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'group_chat'
        db_table_comment = 'This Table Is Used To Store Groups for the Chat On the System'


class ProjectMembers(models.Model):
    member_id = models.AutoField(db_column='Member_ID', primary_key=True)  # Field name made lowercase.
    project = models.ForeignKey('Projects', models.DO_NOTHING, db_column='Project_ID')  # Field name made lowercase.
    leader = models.ForeignKey('Users', models.DO_NOTHING, db_column='Leader_ID')  # Field name made lowercase.
    user_name = models.CharField(db_column='User_Name', max_length=75)  # Field name made lowercase.
    status = models.CharField(db_column='status', max_length=75) 
    user = models.ForeignKey(User, models.DO_NOTHING, db_column='User_ID', related_name='projectmembers_user_set')  # Field name made lowercase.
    created_at = models.DateTimeField(db_column='Created_At')  # Field name made lowercase.
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'project_members'
        db_table_comment = 'This Table Is Used To Store Project Member Details On the System'


class Projects(models.Model):
    project_id = models.AutoField(db_column='Project_ID', primary_key=True)  # Field name made lowercase.
    leader = models.ForeignKey('Users', models.DO_NOTHING, db_column='Leader_ID')  # Field name made lowercase.
    project_name = models.CharField(db_column='Project_Name', max_length=75)  # Field name made lowercase.
    project_details = models.CharField(db_column='Project_Details', max_length=255)  # Field name made lowercase.
    project_image = models.CharField(db_column='Project_Image', max_length=75)  # Field name made lowercase.
    created_at = models.DateTimeField(db_column='Created_At')  # Field name made lowercase.
    updated_at = models.DateTimeField(db_column='Updated_At', blank=True, null=True)  # Field name made lowercase.
    start_date = models.DateField(db_column='Start_Date')  # Field name made lowercase.
    end_date = models.DateField(db_column='End_Date')  # Field name made lowercase.
    total_days = models.IntegerField(db_column='Total_Days')  # Field name made lowercase.
    estimated_budget = models.FloatField(db_column='Estimated_Budget')  # Field name made lowercase.
    actual_expenditure = models.FloatField(db_column='Actual_Expenditure')  # Field name made lowercase.
    balance = models.FloatField(db_column='Balance')  # Field name made lowercase.
    project_status = models.CharField(db_column='Project_Status', max_length=9)  # Field name made lowercase.
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'projects'
        db_table_comment = 'This Table Is Used To Store Project Details For the System'


class Resources(models.Model):
    resource_id = models.AutoField(db_column='Resource_ID', primary_key=True)  # Field name made lowercase.
    user = models.ForeignKey(User, models.DO_NOTHING, db_column='User_ID')  # Field name made lowercase.
    project = models.ForeignKey(Projects, models.DO_NOTHING, db_column='Project_ID')  # Field name made lowercase.
    resource_name = models.CharField(db_column='Resource_Name', max_length=75)  # Field name made lowercase.
    resource_details = models.CharField(db_column='Resource_Details', max_length=80)  # Field name made lowercase.
    resource_directory = models.CharField(db_column='Resource_Directory', max_length=75)  # Field name made lowercase.
    created_at = models.DateTimeField(db_column='Created_At')  # Field name made lowercase.
    updated_at = models.DateTimeField(db_column='Updated_At', blank=True, null=True)  # Field name made lowercase.
    resource_status = models.CharField(db_column='Resource_Status', max_length=10)  # Field name made lowercase.
    resource_type = models.CharField(db_column='Resource_Type', max_length=8)  # Field name made lowercase.
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'resources'
        db_table_comment = 'This Table Is Used To Store Resource Details On the System'


class Tasks(models.Model):
    task_id = models.AutoField(db_column='Task_ID', primary_key=True)  # Field name made lowercase.
    leader = models.ForeignKey(User, models.DO_NOTHING, db_column='Leader_ID')  # Field name made lowercase.
    member = models.ForeignKey(User, models.DO_NOTHING, db_column='Member_ID', related_name='tasks_member_set')  # Field name made lowercase.
    project = models.ForeignKey(Projects, models.DO_NOTHING, db_column='Project_ID')  # Field name made lowercase.
    dependant_task_id = models.IntegerField(db_column='Dependant_Task_ID', blank=True, null=True)  # Field name made lowercase.
    task_name = models.CharField(db_column='Task_Name', max_length=75)  # Field name made lowercase.
    task_details = models.CharField(db_column='Task_Details', max_length=80)  # Field name made lowercase.
    task_given_date = models.DateField(db_column='Task_Given_Date')  # Field name made lowercase.
    task_due_date = models.DateField(db_column='Task_Due_Date')  # Field name made lowercase.
    task_completed_date = models.DateField(db_column='Task_Completed_Date', blank=True, null=True)  # Field name made lowercase.
    task_days_left = models.IntegerField(db_column='Task_Days_Left')  # Field name made lowercase.
    task_days_overdue = models.IntegerField(db_column='Task_Days_Overdue')  # Field name made lowercase.
    task_percentage_complete = models.FloatField(db_column='Task_Percentage_Complete')  # Field name made lowercase.
    task_status = models.CharField(db_column='Task_Status', max_length=15)  # Field name made lowercase.
    created_at = models.DateTimeField(db_column='Created_At')  # Field name made lowercase.
    updated_at = models.DateTimeField(db_column='Updated_At', blank=True, null=True)  # Field name made lowercase.
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tasks'
        db_table_comment = 'This Table Is Used To Store Task Details On the System'


class Transactions(models.Model):
    transaction_id = models.AutoField(db_column='Transaction_ID', primary_key=True)  # Field name made lowercase.
    user = models.ForeignKey(User, models.DO_NOTHING, db_column='User_ID')  # Field name made lowercase.
    project = models.ForeignKey(Projects, models.DO_NOTHING, db_column='Project_ID')  # Field name made lowercase.
    transaction_name = models.CharField(db_column='Transaction_Name', max_length=75)  # Field name made lowercase.
    transaction_details = models.CharField(db_column='Transaction_Details', max_length=80)  # Field name made lowercase.
    transaction_price = models.FloatField(db_column='Transaction_Price')  # Field name made lowercase.
    transaction_quantity = models.IntegerField(db_column='Transaction_Quantity')  # Field name made lowercase.
    transaction_votes_for = models.IntegerField(db_column='Transaction_Votes_For')  # Field name made lowercase.
    transaction_votes_against = models.IntegerField(db_column='Transaction_Votes_Against')  # Field name made lowercase.
    total_transaction_price = models.FloatField(db_column='Total_Transaction_Price')  # Field name made lowercase.
    created_at = models.DateTimeField(db_column='Created_At')  # Field name made lowercase.
    updated_at = models.DateTimeField(db_column='Updated_At', blank=True, null=True)  # Field name made lowercase.
    transaction_status = models.CharField(db_column='Transaction_Status', max_length=9)  # Field name made lowercase.
    is_deleted = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'transactions'
        db_table_comment = 'This Table Is Used To Store Transaction Details On the System'


class TransactionVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transactions, on_delete=models.CASCADE)
    vote = models.BooleanField()  # True for 'for', False for 'against'
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'transaction')

class Users(models.Model):
    user_id = models.AutoField(db_column='User_ID', primary_key=True)  # Field name made lowercase.
    fullname = models.CharField(db_column='Fullname', max_length=75)  # Field name made lowercase.
    gender = models.CharField(db_column='Gender', max_length=6)  # Field name made lowercase.
    phone_number = models.JSONField(db_column='Phone_Number')  # Field name made lowercase.
    email_address = models.CharField(db_column='Email_Address', unique=True, max_length=75)  # Field name made lowercase.
    profile_picture = models.CharField(db_column='Profile_Picture', max_length=75)  # Field name made lowercase.
    user_type = models.CharField(db_column='User_Type', max_length=13)  # Field name made lowercase.
    created_at = models.DateTimeField(db_column='Created_At')  # Field name made lowercase.
    updated_at = models.DateTimeField(db_column='Updated_At', blank=True, null=True)  # Field name made lowercase.
    is_deleted = models.IntegerField()
    online = models.IntegerField()
    password = models.CharField(db_column='Password', max_length=80)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'users'
        db_table_comment = 'This Table Is Used To Store User Details For the System'
