# Generated by Django 5.0.6 on 2024-09-01 07:32

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitesyncApp', '0005_alter_bookmarks_timestamp_alter_chat_timestamp'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chat',
            name='is_bookmarked',
        ),
        migrations.AlterField(
            model_name='bookmarks',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 1, 10, 32, 55, 871622)),
        ),
        migrations.AlterField(
            model_name='chat',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 1, 10, 32, 55, 871622)),
        ),
    ]
