# Generated by Django 3.2.6 on 2022-01-09 04:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0023_auto_20220109_0832'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coworking_slot',
            name='registration_date',
            field=models.DateField(verbose_name='Дата бронирования'),
        ),
        migrations.AlterField(
            model_name='coworking_slot',
            name='registration_time',
            field=models.TimeField(verbose_name='Время броирования'),
        ),
    ]
