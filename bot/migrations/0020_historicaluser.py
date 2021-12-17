# Generated by Django 3.2.6 on 2021-11-23 08:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bot', '0019_alter_issue_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalUser',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('id_telegram', models.BigIntegerField(verbose_name='Телеграм')),
                ('first_name', models.CharField(max_length=100, verbose_name='Имя')),
                ('last_name', models.CharField(max_length=100, verbose_name='Фамилия ')),
                ('type', models.CharField(choices=[('private_person', 'Физическое лицо'), ('company', 'Юридическое лицо')], max_length=15, verbose_name='Тип')),
                ('organization', models.CharField(blank=True, max_length=100, null=True, verbose_name='Организация')),
                ('email', models.EmailField(max_length=254, verbose_name='Почта')),
                ('phone', models.CharField(max_length=32, verbose_name='Телефон')),
                ('registration_date', models.DateField(verbose_name='Дата регистрации')),
                ('registration_time', models.TimeField(verbose_name='Время регистрации')),
                ('status', models.CharField(choices=[('waiting_approval', 'На рассмотрении'), ('approval', 'Одобрен'), ('not_approved', 'Отклонен'), ('deleted', 'Удален')], default=('waiting_approval', 'На рассмотрении'), max_length=20, verbose_name='Статус')),
                ('comment', models.TextField(blank=True, null=True, verbose_name='Комментарий')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical Пользователь',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
