# Generated by Django 3.2.6 on 2021-09-27 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0009_alter_user_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(max_length=32, verbose_name='Телефон'),
        ),
    ]
