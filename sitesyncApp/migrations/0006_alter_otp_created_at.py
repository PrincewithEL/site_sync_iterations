# Generated by Django 5.0.6 on 2024-07-04 18:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitesyncApp', '0005_alter_profile_user_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='created_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
