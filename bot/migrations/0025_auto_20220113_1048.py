# Generated by Django 3.2.6 on 2022-01-13 06:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0024_auto_20220109_0833'),
    ]

    operations = [
        migrations.RenameField(
            model_name='coworking_slot',
            old_name='status_slot',
            new_name='status',
        ),
        migrations.RenameField(
            model_name='event',
            old_name='status_event',
            new_name='status',
        ),
    ]
