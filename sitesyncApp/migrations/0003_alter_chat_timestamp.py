# Generated by Django 5.0.6 on 2024-08-30 20:21

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitesyncApp', '0002_chat_is_bookmarked_chat_is_pinned_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 8, 30, 20, 21, 32, 775847, tzinfo=datetime.timezone.utc)),
        ),
    ]
