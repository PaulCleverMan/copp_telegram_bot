# Generated by Django 3.2.6 on 2021-09-26 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0003_auto_20210926_1344'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='organization',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Организация'),
        ),
    ]