# Generated by Django 5.0.6 on 2024-08-25 17:50

import datetime
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True)),
            ],
            options={
                'db_table': 'auth_group',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthGroupPermissions',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'auth_group_permissions',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('codename', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'auth_permission',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('is_superuser', models.IntegerField()),
                ('username', models.CharField(max_length=150, unique=True)),
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150)),
                ('email', models.CharField(max_length=254)),
                ('is_staff', models.IntegerField()),
                ('is_active', models.IntegerField()),
                ('date_joined', models.DateTimeField()),
            ],
            options={
                'db_table': 'auth_user',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthUserGroups',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'auth_user_groups',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthUserUserPermissions',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'auth_user_user_permissions',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DjangoAdminLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_time', models.DateTimeField()),
                ('object_id', models.TextField(blank=True, null=True)),
                ('object_repr', models.CharField(max_length=200)),
                ('action_flag', models.SmallIntegerField()),
                ('change_message', models.TextField()),
            ],
            options={
                'db_table': 'django_admin_log',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DjangoContentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app_label', models.CharField(max_length=100)),
                ('model', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'django_content_type',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DjangoMigrations',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('app', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('applied', models.DateTimeField()),
            ],
            options={
                'db_table': 'django_migrations',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DjangoSession',
            fields=[
                ('session_key', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('session_data', models.TextField()),
                ('expire_date', models.DateTimeField()),
            ],
            options={
                'db_table': 'django_session',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='GroupChat',
            fields=[
                ('group_id', models.AutoField(primary_key=True, serialize=False)),
                ('leader_id', models.IntegerField()),
                ('group_name', models.CharField(max_length=75)),
                ('group_image', models.CharField(blank=True, max_length=75, null=True)),
                ('is_deleted', models.IntegerField()),
            ],
            options={
                'db_table': 'group_chat',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Users',
            fields=[
                ('user_id', models.AutoField(primary_key=True, serialize=False)),
                ('fullname', models.CharField(max_length=75)),
                ('gender', models.CharField(max_length=6)),
                ('phone_number', models.CharField(max_length=15)),
                ('email_address', models.CharField(max_length=75, unique=True)),
                ('profile_picture', models.CharField(max_length=75)),
                ('user_type', models.CharField(max_length=13)),
                ('created_at', models.DateTimeField()),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.IntegerField()),
                ('online', models.IntegerField()),
                ('password', models.CharField(max_length=80)),
            ],
            options={
                'db_table': 'users',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('chat_id', models.AutoField(primary_key=True, serialize=False)),
                ('message', models.TextField()),
                ('reply', models.TextField(blank=True, null=True)),
                ('scheduled_at', models.TextField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(default=datetime.datetime(2024, 8, 25, 17, 50, 49, 556926, tzinfo=datetime.timezone.utc))),
                ('is_deleted', models.IntegerField()),
                ('file', models.TextField(blank=True, null=True)),
                ('sender_user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='sitesyncApp.groupchat')),
            ],
            options={
                'db_table': 'chat',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='ChatStatus',
            fields=[
                ('status_id', models.AutoField(primary_key=True, serialize=False)),
                ('user_id', models.IntegerField()),
                ('status', models.IntegerField()),
                ('is_deleted', models.IntegerField()),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='sitesyncApp.chat')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='sitesyncApp.groupchat')),
            ],
            options={
                'db_table': 'chat_status',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='BookmarkChat',
            fields=[
                ('bookmark_id', models.AutoField(primary_key=True, serialize=False)),
                ('timestamp', models.DateTimeField()),
                ('is_deleted', models.IntegerField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='sitesyncApp.chat')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='sitesyncApp.groupchat')),
            ],
            options={
                'db_table': 'bookmark_chat',
                'db_table_comment': 'This Table Is Used To Store The Bookmarked Chats On the System',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='OTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('otp_code', models.CharField(max_length=6, unique=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('used', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PinnedChat',
            fields=[
                ('pinned_id', models.AutoField(primary_key=True, serialize=False)),
                ('timestamp', models.DateTimeField()),
                ('is_deleted', models.IntegerField()),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='sitesyncApp.chat')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='sitesyncApp.groupchat')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'pinned_chat',
                'db_table_comment': 'This Table Is Used To Store The Pinned Chats On the System',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(blank=True, max_length=15, null=True)),
                ('gender', models.CharField(blank=True, max_length=10, null=True)),
                ('user_type', models.CharField(choices=[('client', 'Client'), ('contractor', 'Contractor'), ('quantity surveyor', 'Quantity Surveyor'), ('project manager', 'Project Manager'), ('architect', 'Architect'), ('engineer', 'Engineer'), ('admin', 'Administrator')], max_length=50)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_pictures/')),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Projects',
            fields=[
                ('project_id', models.AutoField(primary_key=True, serialize=False)),
                ('project_name', models.CharField(max_length=75)),
                ('project_details', models.CharField(max_length=255)),
                ('project_image', models.CharField(max_length=75)),
                ('created_at', models.DateTimeField()),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('total_days', models.IntegerField()),
                ('estimated_budget', models.FloatField()),
                ('actual_expenditure', models.FloatField()),
                ('balance', models.FloatField()),
                ('project_status', models.CharField(max_length=9)),
                ('is_deleted', models.IntegerField()),
                ('leader', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'projects',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='ProjectMembers',
            fields=[
                ('member_id', models.AutoField(primary_key=True, serialize=False)),
                ('user_name', models.CharField(max_length=75)),
                ('status', models.CharField(max_length=75)),
                ('created_at', models.DateTimeField()),
                ('is_deleted', models.IntegerField()),
                ('leader', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='projectmembers_user_set', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='sitesyncApp.projects')),
            ],
            options={
                'db_table': 'project_members',
                'managed': True,
            },
        ),
        migrations.AddField(
            model_name='groupchat',
            name='project',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='groupchat', to='sitesyncApp.projects'),
        ),
        migrations.CreateModel(
            name='Events',
            fields=[
                ('event_id', models.AutoField(primary_key=True, serialize=False)),
                ('event_name', models.CharField(max_length=75)),
                ('event_details', models.CharField(max_length=80)),
                ('event_date', models.DateField()),
                ('event_start_time', models.TimeField()),
                ('event_end_time', models.TimeField()),
                ('event_location', models.CharField(blank=True, max_length=75, null=True)),
                ('event_link', models.CharField(blank=True, max_length=80, null=True)),
                ('event_status', models.CharField(max_length=9)),
                ('created_at', models.DateTimeField()),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.IntegerField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='sitesyncApp.projects')),
            ],
            options={
                'db_table': 'events',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Resources',
            fields=[
                ('resource_id', models.AutoField(primary_key=True, serialize=False)),
                ('resource_name', models.CharField(max_length=75)),
                ('resource_details', models.CharField(max_length=80)),
                ('resource_directory', models.CharField(max_length=75)),
                ('created_at', models.DateTimeField()),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('resource_status', models.CharField(max_length=10)),
                ('resource_type', models.CharField(max_length=8)),
                ('resource_size', models.CharField(max_length=8)),
                ('is_deleted', models.IntegerField()),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='sitesyncApp.projects')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'resources',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Tasks',
            fields=[
                ('task_id', models.AutoField(primary_key=True, serialize=False)),
                ('dependant_task_id', models.IntegerField(blank=True, null=True)),
                ('task_name', models.CharField(max_length=75)),
                ('task_details', models.CharField(max_length=80)),
                ('task_given_date', models.DateField()),
                ('task_due_date', models.DateField()),
                ('task_completed_date', models.DateField(blank=True, null=True)),
                ('task_days_left', models.IntegerField()),
                ('task_days_overdue', models.IntegerField()),
                ('task_percentage_complete', models.FloatField()),
                ('task_status', models.CharField(max_length=15)),
                ('created_at', models.DateTimeField()),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('is_deleted', models.IntegerField()),
                ('leader', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='tasks_member_set', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='sitesyncApp.projects')),
            ],
            options={
                'db_table': 'tasks',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Transactions',
            fields=[
                ('transaction_id', models.AutoField(primary_key=True, serialize=False)),
                ('transaction_name', models.CharField(max_length=75)),
                ('transaction_details', models.CharField(max_length=80)),
                ('transaction_price', models.FloatField()),
                ('transaction_quantity', models.IntegerField()),
                ('transaction_votes_for', models.IntegerField()),
                ('transaction_votes_against', models.IntegerField()),
                ('total_transaction_price', models.FloatField()),
                ('created_at', models.DateTimeField()),
                ('transaction_date', models.CharField(max_length=15)),
                ('transaction_time', models.CharField(max_length=15)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('transaction_status', models.CharField(max_length=9)),
                ('is_deleted', models.IntegerField()),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='sitesyncApp.projects')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'transactions',
                'managed': True,
            },
        ),
    ]
