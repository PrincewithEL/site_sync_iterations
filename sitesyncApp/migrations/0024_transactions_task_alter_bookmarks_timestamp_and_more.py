# Generated by Django 5.1.1 on 2024-10-17 18:17

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitesyncApp', '0023_tasks_task_transaction_price_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transactions',
            name='task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='sitesyncApp.tasks'),
        ),
        migrations.AlterField(
            model_name='bookmarks',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 10, 17, 21, 17, 4, 768644)),
        ),
        migrations.AlterField(
            model_name='chat',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2024, 10, 17, 21, 17, 4, 769664)),
        ),
    ]
