# Generated by Django 5.0.6 on 2024-09-03 09:41

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitesyncApp', '0011_remove_bookmarkchat_chat_remove_bookmarkchat_group_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookmarks',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 3, 12, 41, 55, 905954)),
        ),
        migrations.AlterField(
            model_name='chat',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 3, 12, 41, 55, 905954)),
        ),
        migrations.AlterField(
            model_name='chat',
            name='updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]