from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords


import logging
logger = logging.getLogger(__name__)

# Create your models here.
class User(models.Model):
    VERIFICATION = (
        ('waiting_approval', 'На рассмотрении'),
        ('approval', 'Одобрен'),
        ('not_approved', 'Отклонен'),
        ('deleted', 'Удален'),
    )
    TYPE_USER = (
        ('private_person', 'Физическое лицо'),
        ('company', 'Юридическое лицо'),
    )
    id_telegram = models.BigIntegerField('Телеграм')
    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия ', max_length=100)
    type = models.CharField('Тип', max_length=15, choices=TYPE_USER)
    organization = models.CharField('Организация', max_length=100, blank=True, null=True)
    email = models.EmailField('Почта')
    phone = models.CharField('Телефон', max_length=32)
    registration_date = models.DateField('Дата регистрации')
    registration_time = models.TimeField('Время регистрации')
    status = models.CharField('Статус', max_length=20, choices=VERIFICATION, default=VERIFICATION[0])
    comment = models.TextField('Комментарий', blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'



class Room(models.Model):
    name_room = models.CharField('Наименование помещения', max_length=100)
    max_people = models.IntegerField('Максимальное количество участников')
    description_room = models.TextField('Описание')
    is_coworking = models.BooleanField(default=False, verbose_name='Коворкинг')

    def __str__(self):
        return f'{self.name_room}'

    class Meta:
        verbose_name = 'Помещение'
        verbose_name_plural = 'Помещения'

class Name_item(models.Model):
    name_item = models.CharField('Наименование предмета', max_length=100)

    def __str__(self):
        return f'{self.name_item}'

    class Meta:
        verbose_name = 'Наименование оборудования'
        verbose_name_plural = 'Наименование оборудований'

class Count_item(models.Model):
    room_id = models.ForeignKey('Room', on_delete=models.CASCADE, verbose_name='Помещение')
    item_id = models.ForeignKey('Name_item', on_delete=models.CASCADE, verbose_name='Наименование предмета')
    count_item = models.IntegerField('Количество')

    def __str__(self):
        return f'{self.room_id}'

    class Meta:
        verbose_name = 'Оборудования'
        verbose_name_plural = 'Оборудования'

class Event(models.Model):
    VERIFICATION_EVENT = (
        ('waiting_approval', 'На рассмотрении'),
        ('approval', 'Одобрено'),
        ('active', 'Активно'),
        ('completed', 'Завершено'),
        ('canceled', 'Отменено'),
    )

    name_event = models.CharField('Наименование мероприятия', max_length=255)
    user_id = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='Пользователь')
    organization = models.CharField('Организация', max_length=100)
    room_id = models.ForeignKey('Room', on_delete=models.CASCADE, verbose_name='Помещение')
    quantity_people = models.IntegerField('Количество участников')
    date = models.DateField('Дата')
    start_time = models.TimeField('Время начала')
    finish_time = models.TimeField('Время окончания')
    status = models.CharField('Статус', max_length=40, choices=VERIFICATION_EVENT, default=VERIFICATION_EVENT[0])
    registration_date = models.DateField('Дата бронирования')
    registration_time = models.TimeField('Время броирования')

    def __str__(self):
        return f'{self.name_event}'

    class Meta:
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'

class Coworking_Slot(models.Model):
    VERIFICATION_SLOT = (
        ('waiting_approval', 'На рассмотрении'),
        ('approval', 'Одобрен'),
        ('active', 'Активен'),
        ('completed', 'Завершен'),
        ('canceled', 'Отменен'),
    )

    number_slot = models.BigIntegerField('Номер слота')
    user_id_created = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='Создал')
    quantity_people = models.IntegerField('Количество участников')
    room_id = models.ForeignKey('Room', on_delete=models.CASCADE, verbose_name='Помещение')
    date = models.DateField('Дата')
    start_time = models.TimeField('Время начала')
    finish_time = models.TimeField('Время окончания')
    status = models.CharField('Статус', max_length=20, choices=VERIFICATION_SLOT, default=VERIFICATION_SLOT[0])
    registration_date = models.DateField('Дата бронирования')
    registration_time = models.TimeField('Время броирования')

    def __str__(self):
        return f'{self.number_slot}'


    class Meta:
        verbose_name = 'Коворкинг (слот)'
        verbose_name_plural = 'Коворкинг (слоты)'

class Coworking_People(models.Model):
    VERIFICATION_PEOPLE = (
        ('waiting_approval', 'На рассмотрении'),
        ('approval', 'Одобрен'),
        ('canceled', 'Отменен'),
    )

    slot_id = models.ForeignKey('Coworking_Slot', on_delete=models.CASCADE, verbose_name='Слот')
    full_name = models.CharField('Ф.И.О', max_length=255)
    email = models.EmailField('Почта')
    phone = models.CharField('Телефон', max_length=11)
    user_id_add = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='Добавил')
    status_people = models.CharField('Статус', max_length=20, choices=VERIFICATION_PEOPLE, default=VERIFICATION_PEOPLE[0])
    visited = models.BooleanField(default=False, verbose_name='Присутствовал')

    def __str__(self):
        return f'{self.full_name}'

    class Meta:
        verbose_name = 'Коворкинг (участники)'
        verbose_name_plural = 'Коворкинг (участники)'


class Issue(models.Model):
    STATUS_ISSUE = (
        ('Pending', 'На рассмотрении'),
        ('Solved', 'Решено'),
        ('Failed', 'Неудачно'),
    )

    TYPE_ISSUE = (
        ('Other', 'Другое'),
        ('Notification', 'Оповещение всех пользователей'),
        ('Notification_company', 'Оповещение для юридических лиц'),
        ('Notification_private_person', 'Оповещение для физических лиц'),
        ('Rejected_registration', 'Отклонено в регистрации'),
        ('Delete_profile', 'Удаление профиля'),
        ('Rejected_booking', 'Отклонено в бронирование помещения'),
        ('Rejected_coworking_slot', 'Отклонено в бронирование коворкинг слота'),
        ('Rejected_coworking_human', 'Отклонено в записи на коворкинг'),
    )

    user_id = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='Пользователь', blank=True, null=True)
    type = models.CharField('Тип', max_length=50, choices=TYPE_ISSUE, default=TYPE_ISSUE[1])
    connection = models.ForeignKey('Connection', on_delete=models.CASCADE, verbose_name='Связь', blank=True, null=True)
    message_id =  models.BigIntegerField('Телеграм', blank=True, null=True)
    message_from_user = models.TextField('Сообщение от пользователя', blank=True, null=True)
    message_from_employee = models.TextField('Сообщение от сотрудника', blank=True, null=True)
    date = models.DateField('Дата')
    time = models.TimeField('Время')
    status = models.CharField('Статус', max_length=20, choices=STATUS_ISSUE, default=STATUS_ISSUE[0])

    def __str__(self):
        return f'{self.user_id}'

    class Meta:
        verbose_name = 'Проблема'
        verbose_name_plural = 'Проблемы'

class Connection(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, verbose_name='Пользователь', blank=True, null=True)
    event = models.OneToOneField('Event', on_delete=models.CASCADE, verbose_name='Мероприятие', blank=True, null=True)
    coworking_slot = models.OneToOneField('Coworking_Slot', on_delete=models.CASCADE, verbose_name='Коворкинг (слот)', blank=True, null=True)
    coworking_people = models.OneToOneField('Coworking_People', on_delete=models.CASCADE, verbose_name='Коворкинг (участники)', blank=True, null=True)

    def __str__(self):
        if self.user_id is not None:
            return f'{self.user}'
        elif self.event_id is not None:
            return f'{self.event}'
        elif self.coworking_slot_id is not None:
            return f'{self.coworking_slot}'
        elif self.coworking_people_id is not None:
            return f'{self.coworking_people}'


    class Meta:
        verbose_name = 'Связь'
        verbose_name_plural = 'Связи'

