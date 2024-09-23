# Generated by Django 5.0.6 on 2024-09-23 01:05

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitesyncApp', '0021_remove_bookmarkchat_chat_remove_bookmarkchat_group_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bookmarkchat',
            name='chat',
        ),
        migrations.RemoveField(
            model_name='bookmarkchat',
            name='group',
        ),
        migrations.RemoveField(
            model_name='bookmarkchat',
            name='user',
        ),
        migrations.DeleteModel(
            name='PinnedChat',
        ),
        migrations.AlterField(
            model_name='bookmarks',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 23, 4, 5, 12, 205600)),
        ),
        migrations.AlterField(
            model_name='chat',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 23, 4, 5, 12, 208858)),
        ),
        migrations.DeleteModel(
            name='BookmarkChat',
        ),
    ]
