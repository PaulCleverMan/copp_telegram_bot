# Generated by Django 3.2.6 on 2022-01-21 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0026_remove_coworking_slot_number_slot'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coworking_people',
            name='phone',
            field=models.CharField(max_length=32, verbose_name='Телефон'),
        ),
    ]
