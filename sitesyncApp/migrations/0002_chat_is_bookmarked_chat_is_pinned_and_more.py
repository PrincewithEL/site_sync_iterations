# Generated by Django 5.0.6 on 2024-08-30 20:05

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitesyncApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='is_bookmarked',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='chat',
            name='is_pinned',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='chat',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 8, 30, 20, 5, 36, 920989, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='projects',
            name='is_deleted',
            field=models.IntegerField(default=0),
        ),
    ]
