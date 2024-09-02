# Generated by Django 5.0.6 on 2024-09-01 23:45

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitesyncApp', '0009_remove_bookmarkchat_chat_remove_bookmarkchat_group_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookmarks',
            name='project_id',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='bookmarks',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 2, 2, 45, 53, 129455)),
        ),
        migrations.AlterField(
            model_name='chat',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 2, 2, 45, 53, 129455)),
        ),
    ]
