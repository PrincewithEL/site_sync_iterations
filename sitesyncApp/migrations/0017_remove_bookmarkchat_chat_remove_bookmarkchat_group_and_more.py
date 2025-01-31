# Generated by Django 5.0.6 on 2024-09-06 15:25

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitesyncApp', '0016_remove_bookmarkchat_chat_remove_bookmarkchat_group_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='logged_in',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='users',
            name='logged_out',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='bookmarks',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 6, 18, 25, 51, 289478)),
        ),
        migrations.AlterField(
            model_name='chat',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 6, 18, 25, 51, 289478)),
        ),
    ]
