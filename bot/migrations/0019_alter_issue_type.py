# Generated by Django 3.2.6 on 2021-10-02 08:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0018_alter_issue_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issue',
            name='type',
            field=models.CharField(choices=[('Other', 'Другое'), ('Notification', 'Оповещение всех пользователей'), ('Notification_company', 'Оповещение для юридических лиц'), ('Notification_private_person', 'Оповещение для физических лиц'), ('Rejected_registration', 'Отклонено в регистрации'), ('Delete_profile', 'Удаление профиля'), ('Rejected_booking', 'Отклонено в бронирование помещения'), ('Rejected_coworking_slot', 'Отклонено в бронирование коворкинг слота'), ('Rejected_coworking_human', 'Отклонено в записи на коворкинг')], default=('Notification', 'Оповещение всех пользователей'), max_length=50, verbose_name='Тип'),
        ),
    ]