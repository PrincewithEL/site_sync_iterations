# Generated by Django 5.0.6 on 2024-09-01 07:29

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitesyncApp', '0004_bookmarks_remove_pinnedchat_chat_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookmarks',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 1, 10, 29, 47, 795637)),
        ),
        migrations.AlterField(
            model_name='chat',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 1, 10, 29, 47, 795637)),
        ),
    ]