# Generated by Django 5.0.6 on 2024-09-03 11:33

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitesyncApp', '0013_remove_bookmarkchat_chat_remove_bookmarkchat_group_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookmarks',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 3, 14, 33, 56, 29278)),
        ),
        migrations.AlterField(
            model_name='chat',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 3, 14, 33, 56, 30275)),
        ),
        migrations.AlterField(
            model_name='chat',
            name='updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]