# Generated by Django 3.2.6 on 2021-09-26 13:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0004_event_organization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='organization',
            field=models.CharField(max_length=100, verbose_name='Организация'),
        ),
    ]