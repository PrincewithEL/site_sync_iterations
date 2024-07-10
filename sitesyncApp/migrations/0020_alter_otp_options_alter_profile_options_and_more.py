# Generated by Django 5.0.6 on 2024-07-10 21:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sitesyncApp', '0019_auto_20240711_0025'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='otp',
            options={'managed': False},
        ),
        migrations.AlterModelOptions(
            name='profile',
            options={'managed': False},
        ),
        migrations.AlterModelTableComment(
            name='chat',
            table_comment=None,
        ),
        migrations.AlterModelTableComment(
            name='chatstatus',
            table_comment=None,
        ),
        migrations.AlterModelTableComment(
            name='events',
            table_comment=None,
        ),
        migrations.AlterModelTableComment(
            name='groupchat',
            table_comment=None,
        ),
        migrations.AlterModelTableComment(
            name='projectmembers',
            table_comment=None,
        ),
        migrations.AlterModelTableComment(
            name='projects',
            table_comment=None,
        ),
        migrations.AlterModelTableComment(
            name='resources',
            table_comment=None,
        ),
        migrations.AlterModelTableComment(
            name='tasks',
            table_comment=None,
        ),
        migrations.AlterModelTableComment(
            name='transactions',
            table_comment=None,
        ),
        migrations.AlterModelTableComment(
            name='users',
            table_comment=None,
        ),
        migrations.DeleteModel(
            name='TransactionVote',
        ),
    ]
