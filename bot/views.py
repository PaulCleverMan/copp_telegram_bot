from django.shortcuts import render
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from datetime import *
import datetime as dt
import calendar
from dateutil.relativedelta import relativedelta
import requests
import time
from django.db.models import signals
from django.dispatch import receiver
import re

from .models import User, Room, Name_item, Count_item, Event, Coworking_Slot, Coworking_People, Issue, Connection

import telebot
from telebot import apihelper, types

from email_validator import validate_email, EmailNotValidError
import phonenumbers
from phonenumbers import NumberParseException
from phonenumbers import carrier, timezone, geocoder

import logging

logger = logging.getLogger(__name__)

WEBHOOK = 'https://smart-tlt.ru'
bot = telebot.TeleBot(settings.TOKEN, threaded=False, parse_mode='HTML')


# Рендер страницы и отправка запросов боту
@csrf_exempt
def index(request):
    if request.method != 'POST':
        return render(request, 'main/index.html')
    if request.META.get('CONTENT_TYPE') != 'application/json':
        return render(request, 'main/index.html')
    json_string = request.body.decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return HttpResponse(status=200)

# Словарь, в который записываются введенные данные от пользователя во время пошагового обработчика
user_dict = {}
event_dict = {}
question_dict = {}
slot_dict = {}
record_in_slot_dist = {}

# Объекты миграций (PostgreSQL)
room = Room.objects
item_room = Count_item.objects
name_item_room = Name_item.objects
event_status = Event.objects
slot_status = Coworking_Slot.objects
issue = Issue.objects
new_issue = Issue()
connection = Connection()
connection_search = Connection.objects

# Время работы организации (для юр. лиц)
calendar.setfirstweekday(calendar.MONDAY)
start_hour_org = datetime.strptime('06:00:00', '%H:%M:%S').time()
finish_hour_org = datetime.strptime('23:30:00', '%H:%M:%S').time()
max_day_for_booking = 30
start_hour_private = datetime.strptime('09:00:00', '%H:%M:%S').time()
finish_hour_private = datetime.strptime('18:00:00', '%H:%M:%S').time()

year = datetime.now().year

# id чата группы, которой предоставлен доступ.
group_chats_access = [-784439140, -722395699]

# Текста шаблона сообщения от бота
text_messages = {
    'welcome':
        'Для использования бота, требуется зарегистрироваться.\n\n<b>Как вы хотите зарегистрироваться?</b>',
    'private_person_approval':
        'Кабинет физического лица.',
    'company_approval':
        'Кабинет юридического лица.',
    'help':
        'Мы тебе не поможем!',
    'question':
        'Введите ваш вопрос. Специалист ответит вам в ближайшее время. Соблюдайте стиль делового общения, иначе специалист отклонит ваш вопрос и вы не получите ответ.',
    'all':
        'Неожиданый ответ, попробуй еще раз или введи комманду /start',

}

registration_messages = {
    'private_person':
        'Вы будете зарегистрированы  как физическое лицо.\n<b>Следуйте инструкции ниже.</b>',
    'company':
        'Вы будете зарегистрированы  как юридическое лицо.\n<b>Следуйте инструкции ниже.</b>',
    'first_name':
        'Введите ваше имя.',
    'last_name':
        'Введите вашу фамилию.',
    'organization':
        'Введите наименование организации.',
    'email':
        'Введите вашу электронную почту.',
    'phone':
        'Введите ваш телефон.',
    'company_confirm':
        '<b>Пожалуйста, поверьте корректность введеных данных!</b>\nВаше имя: <b>{}</b>\nВаша фамилия: <b>{}</b>\nОрганизация: <b>{}</b>\nВаш email: <b>{}</b>\nВаш телефон: <b>{}</b>\n\n<b>Данные введены корректно?</b>',
    'private_person_confirm':
        '<b>Пожалуйста, поверьте корректность введеных данных!</b>\nВаше имя: <b>{}</b>\nВаша фамилия: <b>{}</b>\nВаш email: <b>{}</b>\nВаш телефон: <b>{}</b>\n\n<b>Данные введены корректно?</b>',
    'account_not_approved':
        'Ваш профиль отклонен!',
    'account_deleted':
        'Ваш профиль удален!',

}
booking = {
    'name_event':
        'Введите наименование мероприятия.',
    'quantity_people':
        'Введите количество участников.',
    'date':
        'Введите дату.\n\nФормат: <i>день.месяц</i> \nПример: <i>20.01 или 1.5</i>',
    'start_time':
        'Введите время начала мероприятия. \n\nФормат: <i>часы:минуты</i> \nПример: <i>10:00 или 10:30</i>',
    'finish_time':
        'Введите время окончания мероприятия. \n\nФормат: <i>часы:минуты</i> \nПример: <i>10:00 или 10:30</i>',
    'booking_confirm_event':
        '<b>Пожалуйста, поверьте корректность введеных данных!</b> \nНаименование: <b>{}</b>\nПомещение: <b>{}</b>\nКол-во участников: <b>{}</b>\nДата: <b>{}</b>\nВремя начала: <b>{}</b>\nВремя окончания: <b>{}</b>',
    'booking_confirm_slot':
        '<b>Пожалуйста, поверьте корректность введеных данных!</b>\nКол-во участников: <b>{}</b>\nДата: <b>{}</b>\nВремя начала: <b>{}</b>\nВремя окончания: <b>{}</b>',
    'approval':
        'Ваша заявка одобрена!\n\nНаименование: <b>{}</b>\nПомещение: <b>{}</b>\nКол-во участников: <b>{}</b>\nДата: <b>{}</b>\nВремя начала: <b>{}</b>\nВремя окончания: <b>{}</b>',
    'canceled':
        '\n\n<b>Ваша заявка:</b>\nНаименование: <b>{}</b>\nПомещение: <b>{}</b>\nКол-во участников: <b>{}</b>\nДата: <b>{}</b>\nВремя начала: <b>{}</b>\nВремя окончания: <b>{}</b>',
}

# callback кнопки
btn_private_person = types.InlineKeyboardButton(text='Физическое лицо', callback_data='private_person')
btn_company = types.InlineKeyboardButton(text='Юридическое лицо', callback_data='company')
btn_yes = types.KeyboardButton('Да')
btn_no = types.KeyboardButton('Нет')
btn_room_event = types.InlineKeyboardButton(text='Бронирование помещений', callback_data='room_event')
btn_start_back = types.InlineKeyboardButton(text='Главное меню', callback_data='start_back')
btn_reg_slot = types.InlineKeyboardButton(text='Бронирование коворгинг', callback_data='reg_slot')
btn_slot_record = types.InlineKeyboardButton(text='Запись в коворгинг', callback_data='slot_record')
btn_slot_record_me = types.InlineKeyboardButton(text='Записаться', callback_data='slot_record_me')
btn_slot_record_other = types.InlineKeyboardButton(text='Записать другого участника', callback_data='slot_record_other')

def chat_group_or_private(chat_id):
    chat_id = chat_id.isdigit()
    return chat_id

def group_command_access(chat_id):
    id = chat_id
    for number in range(len(group_chats_access)):
        if group_chats_access[number] == id:
            return True
    return False

def send_event(chat_id):
    events = event_status.filter(date=datetime.now().date() + timedelta(1), status='approval')
    text_events = ''
    date_text = datetime.strptime(str(datetime.now().date() + timedelta(1)), '%Y-%m-%d').date().strftime('%d.%m.%Y')
    if events.exists() is True:
        for event in range(len(events)):
            text_events += 'Наименование: <b>{}</b>\nПомещение: <b>{}</b>\nВремя: <b>{}</b>\n\n'.format(
                events[event].name_event,
                room.get(id=events[event].room_id_id).name_room,
                f'{events[event].start_time} - {events[event].finish_time}',
            )
        bot.send_message(chat_id, f'Выгрузка <b>{date_text}</b>\n\n' + text_events)
    elif events.exists() is False:
        bot.send_message(chat_id, f'Выгрузка <b>{date_text}</b>\n\nМероприятия не забронированны!')



# Обработка команды (старт) от пользователя работает в зависимости от того, зарегистрирован или нет
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = chat_group_or_private(str(message.chat.id))

    if chat_id:
        user = User.objects.filter(id_telegram=message.chat.id)
        markup = types.InlineKeyboardMarkup()
        if user:
            if user.filter(type='private_person') and user.filter(status='approval'):
                markup.add(btn_reg_slot)
                markup.add(btn_slot_record)
                bot.send_message(message.chat.id, text_messages['private_person_approval'], reply_markup=markup)
            elif user.filter(type='company') and user.filter(status='approval'):
                markup.add(btn_room_event)
                bot.send_message(message.chat.id, text_messages['company_approval'], reply_markup=markup)
            elif user.filter(status='not_approved'):
                bot.send_message(message.chat.id, registration_messages['account_not_approved'])
            elif user.filter(status='deleted'):
                markup.add(btn_private_person, btn_company)
                bot.send_message(message.chat.id, text_messages['welcome'], reply_markup=markup)
            else:
                bot.send_message(message.chat.id, 'Ваш профиль не подтвержден. Пожалуйста, ожидайте.')
        elif not user:
            markup.add(btn_private_person, btn_company)
            bot.send_message(message.chat.id, text_messages['welcome'], reply_markup=markup)
    elif not chat_id:
            bot.send_message(message.chat.id, f'{message.chat.id}')



# Обработка команды (помощь) от пользователя (регистрация не требуется)
@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, text_messages['help'])

# Обработчик комманды на выполнение отправки забронированных помещений.
@bot.message_handler(commands=['list'])
def list(message):
    chat_id = chat_group_or_private(str(message.chat.id))
    if not chat_id:
        access_group = group_command_access(message.chat.id)
        if access_group:
            send_event(message.chat.id)
        elif not access_group:
            bot.send_message(message.chat.id, 'У вас нет доступа к данной комманде!')


# Обработка команды (вопрос) от пользователя (регистрация не требуется)
@bot.message_handler(commands=['question'])
def question(message):
    chat_id = chat_group_or_private(str(message.chat.id))
    if chat_id:
        chat_id = message.chat.id
        question_dict[chat_id] = new_issue
        new_issue.type = 'Other'
        new_issue.message_id = chat_id

        bot.send_message(message.chat.id, text_messages['question'])
        bot.register_next_step_handler(message, first_step_question, question_dict)


def first_step_question(message, question_dict):
    try:
        chat_id = message.chat.id
        new_issue = question_dict[chat_id]
        new_issue.message_from_user = message.text

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(btn_yes, btn_no)

        bot.send_message(message.chat.id,
                         f'Проверьте, вопрос составлен корректно? \n\n<b>Ваш вопрос:</b>\n{new_issue.message_from_user}',
                         reply_markup=markup)
        bot.register_next_step_handler(message, question_confirm, question_dict)
    except Exception as e:
        bot.send_message(message, 'Что-то пошло не так!')


def question_confirm(message, question_dict):
    try:
        markup = types.ReplyKeyboardRemove(selective=False)

        if message.text == 'Да':
            try:
                chat_id = message.chat.id
                new_issue = question_dict[chat_id]
                new_issue.date = datetime.now().date()
                new_issue.time = datetime.now().time()
                new_issue.status = 'Pending'
                new_issue.save()
                bot.send_message(message.chat.id, 'Ваш вопрос отправлен!', reply_markup=markup)
            except Exception as e:
                bot.send_message(message, f'Что-то пошло не так!')
        elif message.text == 'Нет':
            bot.send_chat_action(message.chat.id, 'typing')
            time.sleep(3)
            start(message)
    except Exception as e:
        bot.send_message(message, f'Что-то пошло не так!')


# Ответ на произвольное сообщение от пользователя
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.send_message(message.chat.id, text_messages['all'])


# Обработка любых нажатых кнопок callback
@bot.callback_query_handler(func=lambda call: True)
def call_handler(call):
    markup = types.InlineKeyboardMarkup()
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup='')

    if call.data == 'private_person' or call.data == 'company':
        chat_id = call.message.chat.id
        user = User()
        user_dict[chat_id] = user
        user.id_telegram = call.from_user.id

        if call.data == 'private_person':
            user.type = 'private_person'
            bot.send_message(call.message.chat.id, registration_messages['private_person'])
        elif call.data == 'company':
            user.type = 'company'
            bot.send_message(call.message.chat.id, registration_messages['company'])

        msg = bot.send_message(call.message.chat.id, registration_messages['first_name'])
        bot.register_next_step_handler(msg, first_step_reg, user_dict)

    elif call.data == 'start_back':
        message = call.message
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start(message)

    elif call.data == 'room_event':
        bot.delete_message(call.message.chat.id, call.message.message_id)

        first_room = room.all()[0]

        btn_book = types.InlineKeyboardButton(text='Забронировать', callback_data=f'{0}_book')
        btn_next_start = types.InlineKeyboardButton(text='Вперед', callback_data=f'{1}_next')
        btn_item_room_show = types.InlineKeyboardButton(text='Оборудования', callback_data=f'{0}_item_show')

        markup.add(btn_item_room_show)
        markup.add(btn_book)
        markup.add(btn_next_start)
        markup.add(btn_start_back)

        bot.send_message(
            call.message.chat.id,
            f'\nПомещение: <b>{first_room.name_room}</b>\nУчастники: <b>{first_room.max_people}(max)</b>\nОписание: <b>{first_room.description_room}</b>',
            reply_markup=markup
        )
    #slot
    elif call.data == 'reg_slot':
        chat_id = call.message.chat.id
        main_room = room.get(is_coworking=True).id
        registration_slot(call, chat_id, main_room)
    elif call.data == 'slot_record':
        registration_in_slot_select(call)
    elif call.data == 'slot_record_me' or call.data == 'slot_record_other':
        registration_in_slot(call)

    i = 0
    for el in room.all():
        btn_back = types.InlineKeyboardButton(text='Назад', callback_data=f'{i - 1}_back')
        btn_next = types.InlineKeyboardButton(text='Вперед', callback_data=f'{i + 1}_next')
        btn_item_room_show = types.InlineKeyboardButton(text='Оборудования', callback_data=f'{i}_item_show')
        btn_item_room_hide = types.InlineKeyboardButton(text='Скрыть', callback_data=f'{i}_item_hide')
        btn_book = types.InlineKeyboardButton(text='Забронировать', callback_data=f'{i}_book')

        if call.data == f'{i}_next':
            markup.add(btn_item_room_show)
            markup.add(btn_book)

            next_room = room.all()[i]

            if i + 1 == len(room.all()):
                markup.add(btn_back)
            else:
                markup.add(btn_back, btn_next)
            markup.add(btn_start_back)

            bot.edit_message_text(
                f'\nПомещение: <b>{next_room.name_room}</b>\nУчастники: <b>{next_room.max_people}</b>(max)\nОписание: <b>{next_room.description_room}</b>',
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        elif call.data == f'{i}_back':

            markup.add(btn_item_room_show)
            markup.add(btn_book)

            back_room = room.all()[i]

            if i == 0:
                markup.add(btn_next)
            else:
                markup.add(btn_back, btn_next)
            markup.add(btn_start_back)

            bot.edit_message_text(
                f'\nПомещение: <b>{back_room.name_room}</b>\nУчастники: <b>{back_room.max_people}</b>(max)\nОписание: <b>{back_room.description_room}</b>',
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )

        elif call.data == f'{i}_item_show':
            main_room = room.all()[i].id
            room_item = ''
            for item in item_room.filter(room_id=main_room):
                foreign_id = item.item_id_id
                count_item = item.count_item
                for name in name_item_room.filter(id=foreign_id):
                    room_item = room_item + f'Название: <b>{name.name_item}</b>, количество: <b>{count_item}</b>\n'

            markup.add(btn_item_room_hide)

            bot.send_message(call.message.chat.id, f'Список оборудывания:\n{room_item}', reply_markup=markup)

        elif call.data == f'{i}_item_hide':
            main_room = room.all()[i]

            markup.add(btn_item_room_show)
            markup.add(btn_book)

            if i + 1 == len(room.all()):
                markup.add(btn_back)
            elif i == 0:
                markup.add(btn_next)
            else:
                markup.add(btn_back, btn_next)
            markup.add(btn_start_back)

            bot.delete_message(call.message.chat.id, call.message.message_id - 1)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(
                call.message.chat.id,
                f'\nПомещение: <b>{main_room.name_room}</b>\nУчастники: <b>{main_room.max_people}</b>(max)\nОписание: <b>{main_room.description_room}</b>',
                reply_markup=markup
            )
        #event
        elif call.data == f'{i}_book':
            try:
                main_room = room.all()[i].id
                chat_id = call.message.chat.id

                if room.get(id=main_room).is_coworking:
                    registration_slot(call, chat_id, main_room)
                else:
                    event = Event()
                    event_dict[chat_id] = event
                    event.room_id_id = main_room

                    event.user_id_id = User.objects.get(id_telegram=call.message.chat.id).id
                    event.organization = User.objects.get(id_telegram=call.message.chat.id).organization
                    bot.send_message(call.message.chat.id, booking['date'])
                    bot.register_next_step_handler(call.message, first_step_booking, event_dict, event_status)


            except Exception as e:
                bot.send_message(call.message, f'Что-то пошло не так!\n{e}')
        i = i + 1

# Регистрация пользователей
def first_step_reg(message, user_dict):
    try:
        chat_id = message.chat.id
        user = user_dict[chat_id]
        user.first_name = message.text

        msg = bot.send_message(message.chat.id, registration_messages['last_name'])
        bot.register_next_step_handler(msg, second_step_reg, user_dict)
    except Exception as e:
        bot.send_message(message, 'Что-то пошло не так!')


def second_step_reg(message, user_dict):
    try:
        chat_id = message.chat.id
        user = user_dict[chat_id]
        user.last_name = message.text

        if user.type == 'company':
            msg = bot.send_message(message.chat.id, registration_messages['organization'])
            bot.register_next_step_handler(msg, third_step_reg, user_dict)
        elif user.type == 'private_person':
            msg = bot.send_message(message.chat.id, registration_messages['email'])
            bot.register_next_step_handler(msg, fourth_step_reg, user_dict)
    except Exception as e:
        bot.send_message(message, 'Что-то пошло не так!')


def third_step_reg(message, user_dict):
    try:
        chat_id = message.chat.id
        user = user_dict[chat_id]
        user.organization = message.text

        msg = bot.send_message(message.chat.id, registration_messages['email'])
        bot.register_next_step_handler(msg, fourth_step_reg, user_dict)
    except Exception as e:
        bot.send_message(message, 'Что-то пошло не так!')


def fourth_step_reg(message, user_dict):
    try:
        chat_id = message.chat.id
        user = user_dict[chat_id]

        email = message.text
        valid = validate_email(email)
        user.email = valid.email

        msg = bot.send_message(message.chat.id, registration_messages['phone'])
        bot.register_next_step_handler(msg, fifth_step_reg, user_dict)
    except EmailNotValidError as e:
        bot.send_message(message, 'Некорректный Email, повторите попытку...')
        bot.register_next_step_handler(message.chat.id, fourth_step_reg, user_dict)
    except Exception as e:
        bot.send_message(message, 'Что-то пошло не так!')


def fifth_step_reg(message, user_dict):
    try:
        chat_id = message.chat.id
        user = user_dict[chat_id]
        phone = message.text
        phone_number = phonenumbers.parse(phone, 'RU')
        phone_number = phonenumbers.is_valid_number(phone_number)
        if not phone_number:
            bot.send_message(message.chat.id, 'Некорректный телефон, повторите попытку...')
            bot.register_next_step_handler(message, fifth_step_reg, user_dict)
        else:
            phone_number = phonenumbers.parse(phone, 'RU')
            phone_number = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            user.phone = f'{phone_number}'
            user.status = 'waiting_approval'
            user.registration_date = datetime.now().date()
            user.registration_time = datetime.now().time()

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(btn_yes, btn_no)
            if user.type == 'company':
                bot.send_message(
                    message.chat.id,
                    registration_messages['company_confirm'].format(
                        user.first_name,
                        user.last_name,
                        user.organization,
                        user.email,
                        user.phone),
                    reply_markup=markup)
            elif user.type == 'private_person':
                bot.send_message(
                    message.chat.id,
                    registration_messages['private_person_confirm'].format(
                        user.first_name,
                        user.last_name,
                        user.email,
                        user.phone),
                    reply_markup=markup)

            bot.register_next_step_handler(message, registration_confirm, user_dict)

    except NumberParseException as e:
        bot.send_message(message, 'Некорректный телефон, повторите попытку...')
        bot.register_next_step_handler(message, fifth_step_reg, user_dict)
    except Exception as e:
        bot.send_message(message, f'Что-то пошло не так!')


def registration_confirm(message, user_dict):
    try:
        markup = types.ReplyKeyboardRemove(selective=False)

        if message.text == 'Да':
            try:
                chat_id = message.chat.id
                user = user_dict[chat_id]
                user.save()
                bot.send_message(message.chat.id,
                                 'Вы зарегистрированны! Для продолжения использования бота, пожалуйста, ожидайте одобрения.',
                                 reply_markup=markup)
            except Exception as e:
                bot.send_message(message, f'Что-то пошло не так!')
        elif message.text == 'Нет':
            bot.send_chat_action(message.chat.id, 'typing')
            time.sleep(3)
            start(message)
    except Exception as e:
        bot.send_message(message, f'Что-то пошло не так!')


def rabbit_intervals(date, event, intervals, status_booking, start_work, end_work):
    event_date = status_booking.filter(date=date, room_id_id=event.room_id_id).order_by('start_time')
    event_length = len(status_booking.filter(date=date, room_id_id=event.room_id_id))

    if status_booking.filter(date=date, room_id_id=event.room_id_id).exists() is False:
        intervals = create_table_interval(start_work, end_work, intervals)

    i = 0
    while i < event_length:

        # От начала работы заведения до первого интервала
        if i == 0 and start_work != event_date[0].start_time:
            finish_interval = timedelta(hours=event_date[i].start_time.hour,
                                        minutes=event_date[i].start_time.minute) - timedelta(minutes=30)
            start_interval = start_work
            finish_interval = datetime.strptime(str(finish_interval), '%H:%M:%S').time()
            if finish_interval > start_interval < event_date[i].start_time:
                intervals = create_table_interval(start_interval, finish_interval, intervals)
        # От первого до второго и последующих интервалов
        if i + 1 < event_length:
            finish_interval = timedelta(hours=event_date[i + 1].start_time.hour,
                                        minutes=event_date[i + 1].start_time.minute) - timedelta(minutes=30)
            start_interval = timedelta(hours=event_date[i].finish_time.hour,
                                       minutes=event_date[i].finish_time.minute) + timedelta(minutes=30)
            finish_interval = datetime.strptime(str(finish_interval), '%H:%M:%S').time()
            start_interval = datetime.strptime(str(start_interval), '%H:%M:%S').time()
            if event_date[i].finish_time < start_interval < finish_interval < event_date[i + 1].start_time:
                intervals = create_table_interval(start_interval, finish_interval, intervals)
        # От последнего и до окончания работы заведения
        if i + 1 == event_length and end_work != event_date.reverse()[0].finish_time:
            finish_interval = end_work
            start_interval = timedelta(hours=event_date[i].finish_time.hour,
                                       minutes=event_date[i].finish_time.minute) + timedelta(minutes=30)
            start_interval = datetime.strptime(str(start_interval), '%H:%M:%S').time()
            if finish_interval > start_interval > event_date[i].finish_time:
                intervals = create_table_interval(start_interval, finish_interval, intervals)

        i += 1

    return intervals


def create_table_interval(start_interval, finish_interval, intervals):
    n = len(intervals)
    intervals.append([])
    intervals[n].append(start_interval)
    intervals[n].append(finish_interval)

    return intervals


def string_interval(interval, event_interval_fee):
    j = 0
    while j < len(interval):
        start_time = interval[j][0]
        end_time = interval[j][1]
        event_interval_fee += f'{start_time} - {end_time}\n'
        j += 1

    return event_interval_fee


def date_next_year(date):
    if date < datetime.today().date():
        date += relativedelta(years= +1)
        if datetime.now().date() + timedelta(max_day_for_booking) >= date:
            return True
        elif datetime.now().date() + timedelta(max_day_for_booking) < date:
            return False
    elif datetime.now().date() + timedelta(max_day_for_booking) >= date:
        return True

def formatter_date(message):
    date = message.text + f'.{year}'
    date = datetime.strptime(date, '%d.%m.%Y').date().strftime('%Y-%m-%d')
    date = datetime.strptime(str(date), '%Y-%m-%d').date()
    return date

def days_off(date, dict):
    if room.get(id=dict.room_id_id).is_coworking:
        if date.weekday() == 5 or date.weekday() == 6:
            return False
        else:
            return True
    else:
        return True

# Бронирование помещения
def first_step_booking(message, dict, status_booking):
    try:
        chat_id = message.chat.id
        event = dict[chat_id]

        date = formatter_date(message)
        control_year = date_next_year(date)

        intervals = []
        event_interval_fee = ''

        if room.get(id=event.room_id_id).is_coworking:
            intervals = rabbit_intervals(date, event, intervals, status_booking, start_hour_private, finish_hour_private)
        elif not room.get(id=event.room_id_id).is_coworking:
            intervals = rabbit_intervals(date, event, intervals, status_booking, start_hour_org, finish_hour_org)

        event_interval_fee = string_interval(intervals, event_interval_fee)

        if not control_year:
            bot.send_message(message.chat.id, 'Можно забронировать только на 30 дней вперед! Повторите попытку...')
            bot.register_next_step_handler(message, first_step_booking, dict, status_booking)
        elif control_year:
            if date < datetime.today().date():
                date += relativedelta(years=+1)
            control_day = days_off(date, event)
            if not control_day:
                bot.send_message(message.chat.id, 'Помещение доступно для бронирование только в буднии дни! Повторите попытку...')
                bot.register_next_step_handler(message, first_step_booking, dict, status_booking)
            elif status_booking.filter(date=date, room_id_id=event.room_id_id).exists() is True:

                if event_interval_fee != '':
                    event.date = date
                    bot.send_message(message.chat.id, f"Доступные интервалы для бронирования:\n{event_interval_fee}\nВведите время начала мероприятия. \n\nФормат: <i>часы:минуты</i> \nПример: <i>10:00 или 10:30</i>")
                    bot.register_next_step_handler(message, second_step_booking, dict, intervals, status_booking)
                else:
                    bot.send_message(message.chat.id, 'Помещение забронированно в этот день! Пожалуйста, выбирите другую дату!')
                    bot.register_next_step_handler(message, first_step_booking, dict, status_booking)

            elif status_booking.filter(date=date, room_id_id=event.room_id_id).exists() is False:
                event.date = date
                bot.send_message(message.chat.id, f"Доступные интервалы для бронирования:\n{event_interval_fee}\nВведите время начала мероприятия. \n\nФормат: <i>часы:минуты</i> \nПример: <i>10:00 или 10:30</i>")
                bot.register_next_step_handler(message, second_step_booking, dict, intervals, status_booking)

    except ValueError:
        bot.send_message(message.chat.id, 'Некорректный формат или значение,  повторите попытку...')
        bot.register_next_step_handler(message, first_step_booking, dict, status_booking)
    except Exception as e:
        bot.send_message(message, f'Что-то пошло не так! \n{e}')


def convert_time(string_time):
    string_time = datetime.strptime(string_time, '%H:%M:%S').time()

    return string_time


def validation_interval(time, interval, step_time, start_time=None):
    j = 0
    while j < len(interval):
        first_time = interval[j][0]
        second_time = interval[j][1]

        if step_time == 'start_time':
            if first_time <= time < second_time:
                return True
        elif step_time == 'finish_time':
            if second_time > start_time >= first_time:
                if start_time < time <= second_time:
                    return True
        j += 1
    return False

def opening_hours(time, start_work, end_work):
    if time < start_work or time > end_work:
        return False
    else:
        return True


def second_step_booking(message, dict, intervals, status_booking):
    try:
        chat_id = message.chat.id
        event = dict[chat_id]

        start_time = message.text + ':00'
        start_time = convert_time(start_time)
        check_start_time = True

        if intervals:
            step_time = 'start_time'
            check_start_time = validation_interval(start_time, intervals, step_time)

        if room.get(id=event.room_id_id).is_coworking:
            opening_hours_bol = opening_hours(start_time, start_hour_private, finish_hour_private)
        else:
            opening_hours_bol = opening_hours(start_time, start_hour_org, finish_hour_org)

        if not opening_hours_bol:
            bot.send_message(message.chat.id,
                             'Время мероприятия превышает время работы заведения, повторите попытку...')
            bot.register_next_step_handler(message, second_step_booking, dict, intervals, status_booking)
        elif start_time <= datetime.now().time() and str(event.date) == str(datetime.now().date()):
            bot.send_message(message.chat.id, 'Время не может быть из прошлого, повторите попытку...')
            bot.register_next_step_handler(message, second_step_booking, dict, intervals, status_booking)
        elif start_time.minute is not 0 and start_time.minute is not 30:
            bot.send_message(message.chat.id, 'Интервал времени должен быть равен 30 минут, повторите попытку...')
            bot.register_next_step_handler(message, second_step_booking, dict, intervals, status_booking)
        elif check_start_time is True:
            event.start_time = start_time
            bot.send_message(message.chat.id, booking['finish_time'])
            bot.register_next_step_handler(message, third_step_booking, dict, intervals, status_booking)
        elif check_start_time is False:
            bot.send_message(message.chat.id,
                             'Время забронировано или вы ввели конечное время свободного интервала, повторите попытку...')
            bot.register_next_step_handler(message, second_step_booking, dict, intervals, status_booking)
    except ValueError:
        bot.send_message(message.chat.id, 'Некорректный формат или значение,  повторите попытку...')
        bot.register_next_step_handler(message, second_step_booking, dict, intervals, status_booking)

    except Exception as e:
        bot.send_message(message, f'Что-то пошло не так! \n{e}')


def third_step_booking(message, dict, intervals, status_booking):
    try:
        chat_id = message.chat.id
        event = dict[chat_id]

        finish_time = message.text + ':00'
        finish_time = convert_time(finish_time)

        if finish_time <= event.start_time:
            bot.send_message(message.chat.id, 'Время меньше либо равно началу мероприятия, повторите попытку...')
            bot.register_next_step_handler(message, third_step_booking, dict, intervals, status_booking)
        else:
            check_finish_time = True

            if intervals:
                step_time = 'finish_time'
                check_finish_time = validation_interval(finish_time, intervals, step_time, event.start_time)

            if room.get(id=event.room_id_id).is_coworking:
                opening_hours_bol = opening_hours(finish_time, start_hour_private, finish_hour_private)
            else:
                opening_hours_bol = opening_hours(finish_time, start_hour_org, finish_hour_org)

            if not opening_hours_bol:
                bot.send_message(message.chat.id,
                                 'Время мероприятия превышает время работы заведения, повторите попытку...')
                bot.register_next_step_handler(message, third_step_booking, dict, intervals, status_booking)
            elif finish_time.minute is not 0 and finish_time.minute is not 30:
                bot.send_message(message.chat.id, 'Интервал времени должен быть равен 30 минут, повторите попытку...')
                bot.register_next_step_handler(message, third_step_booking, dict, intervals, status_booking)
            elif check_finish_time is True:
                event.finish_time = finish_time

                if room.get(id=event.room_id_id).is_coworking:
                    bot.send_message(message.chat.id, booking['quantity_people'])
                    bot.register_next_step_handler(message, sixth_step_booking, dict, status_booking)
                else:
                    bot.send_message(message.chat.id, booking['name_event'])
                    bot.register_next_step_handler(message, fourth_step_booking, dict, status_booking)
            elif check_finish_time is False:
                bot.send_message(message.chat.id,
                                 '❗️Конечное время превышает допустимый интервал, повторите попытку...❗️')
                bot.register_next_step_handler(message, third_step_booking, dict, intervals, status_booking)


    except ValueError:
        bot.send_message(message.chat.id, 'Некорректный формат или значение,  повторите попытку...')
        bot.register_next_step_handler(message, third_step_booking, dict, intervals, status_booking)
    except Exception as e:
        bot.send_message(message, f'Что-то пошло не так!\n {e}')


def fourth_step_booking(message, dict, status_booking):
    try:
        chat_id = message.chat.id
        event = dict[chat_id]

        event.name_event = message.text

        bot.send_message(message.chat.id, booking['quantity_people'])
        bot.register_next_step_handler(message, sixth_step_booking, dict, status_booking)
    except Exception as e:
        bot.send_message(message, 'Что-то пошло не так!')


def sixth_step_booking(message, dict, status_booking):
    try:
        chat_id = message.chat.id
        event = dict[chat_id]

        quantity_people = message.text

        if not quantity_people.isdigit():
            bot.send_message(message.chat.id, 'Сообщение должно быть целым числом, повторите попытку...')
            bot.register_next_step_handler(message, sixth_step_booking, dict, status_booking)
        elif int(quantity_people) > room.get(id=event.room_id_id).max_people:
            bot.send_message(message.chat.id, 'Ваше число превышает максимальное количество участников, повторите попытку...')
            bot.register_next_step_handler(message, sixth_step_booking, dict, status_booking)
        elif quantity_people.isdigit() and int(quantity_people) <= room.get(id=event.room_id_id).max_people:
            event.quantity_people = int(quantity_people)

            event.status = 'waiting_approval'
            event.registration_date = datetime.now().date()
            event.registration_time = datetime.now().time()

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(btn_yes, btn_no)
            if room.get(id=event.room_id_id).is_coworking:
                bot.send_message(message.chat.id, booking['booking_confirm_slot'].format(
                    event.quantity_people,
                    datetime.strptime(str(event.date), '%Y-%m-%d').date().strftime('%d.%m.%Y'),
                    event.start_time,
                    event.finish_time),
                                 reply_markup=markup)
            else:
                bot.send_message(message.chat.id, booking['booking_confirm_event'].format(
                    event.name_event,
                    room.get(id=event.room_id_id).name_room,
                    event.quantity_people,
                    datetime.strptime(str(event.date), '%Y-%m-%d').date().strftime('%d.%m.%Y'),
                    event.start_time,
                    event.finish_time),
                                 reply_markup=markup)

            bot.register_next_step_handler(message, booking_confirm, dict, status_booking)

    except Exception as e:
        bot.send_message(message, f'Что-то пошло не так! {e}')


def booking_confirm(message, dict, status_booking):
    try:
        markup = types.ReplyKeyboardRemove(selective=False)

        if message.text == 'Да':
            try:
                chat_id = message.chat.id
                event = dict[chat_id]
                event.save()
                bot.send_message(message.chat.id, 'Заявка на бронирование отправлена! Ожидайте, одобрения.',
                                 reply_markup=markup)
                bot.send_chat_action(message.chat.id, 'typing')
                time.sleep(3)
                start(message)
            except Exception as e:
                bot.send_message(message, f'Что-то пошло не так!')
        elif message.text == 'Нет':
            bot.send_chat_action(message.chat.id, 'typing')
            time.sleep(3)
            start(message)
    except Exception as e:
        bot.send_message(message, f'Что-то пошло не так!')


def registration_slot(call, chat_id, main_room):
    slot = Coworking_Slot()
    slot_dict[chat_id] = slot
    slot.room_id_id = main_room

    slot.user_id_created_id = User.objects.get(id_telegram=call.message.chat.id).id
    bot.send_message(call.message.chat.id, booking['date'])
    bot.register_next_step_handler(call.message, first_step_booking, slot_dict, slot_status)

def registration_in_slot_select(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(btn_slot_record_me, btn_slot_record_other)
    bot.send_message(call.message.chat.id, 'Вы можете записаться на участие в коворкинг самостоятельно или добавить другого участника. Выберите способ записи.', reply_markup = markup)

def registration_in_slot(call):
    bot.send_message(call.message.chat.id, 'Функционал не реализован')


bot.enable_save_next_step_handlers(delay=0,
                                   filename="home/p/pashok13ru/telegram_bot/public_html/.handlers-saves/step.save")
bot.load_next_step_handlers(filename="home/p/pashok13ru/telegram_bot/public_html/.handlers-saves/step.save")


# Уведомление об одобрении или отклонении профиля
@receiver(signals.pre_save, sender=User)
def user_approval(sender, instance, **kwargs):
    try:
        old_status = sender.objects.get(pk=instance.pk)
        if old_status.status != instance.status:
            chat_id = instance.id_telegram
            status = instance.status

            if status == 'approval':
                bot.send_message(chat_id, 'Ваш аккаунт одобрен!')
            elif status == 'not_approved' or status == 'deleted':
                try:
                    new_issue.connection = connection_search.get(user_id=instance.id)
                except Connection.DoesNotExist:
                    connection.user_id = instance.id
                    connection.save()
                finally:
                    new_issue.user_id_id = instance.id
                    new_issue.connection = connection_search.get(user_id=instance.id)
                    if status == 'not_approved':
                        new_issue.type = 'Rejected_registration'
                    if status == 'deleted':
                        new_issue.type = 'Delete_profile'
                    new_issue.date = datetime.now().date()
                    new_issue.time = datetime.now().time()
                    new_issue.status = 'Pending'
                    new_issue.save()
    except User.DoesNotExist:
        return


# Уведомление о подтверждении или отколонении мероприятия
@receiver(signals.pre_save, sender=Event)
def event_approval(sender, instance, **kwargs):
    try:
        old_status = sender.objects.get(pk=instance.pk)
        if old_status.status != instance.status:
            chat_id = User.objects.get(id=instance.user_id_id).id_telegram
            status = instance.status

            if status == 'approval':
                bot.send_message(chat_id, booking['approval'].format(
                    instance.name_event,
                    room.get(id=instance.room_id_id).name_room,
                    instance.quantity_people,
                    datetime.strptime(str(instance.date), '%Y-%m-%d').date().strftime('%d.%m.%Y'),
                    instance.start_time,
                    instance.finish_time))
            elif status == 'canceled':
                try:
                    new_issue.connection = connection_search.get(event_id=instance.id)
                except Connection.DoesNotExist:
                    connection.event_id = instance.id
                    connection.save()
                finally:
                    new_issue.connection = connection_search.get(event_id=instance.id)
                    new_issue.user_id_id = instance.user_id_id
                    new_issue.type = 'Rejected_booking'
                    new_issue.date = datetime.now().date()
                    new_issue.time = datetime.now().time()
                    new_issue.status = 'Pending'
                    new_issue.save()
    except Event.DoesNotExist:
        return


# Оповещение пользователей
@receiver(signals.pre_save, sender=Issue)
def issue_notifications(sender, instance, **kwargs):
    try:
        if instance.message_from_employee is None:
            return
        old_status = sender.objects.get(pk=instance.pk)
        if old_status.status != instance.status and instance.status == 'Solved':
            if instance.type != 'Other' and re.search('Notification', instance.type) is None:
                chat_id = User.objects.get(id=instance.user_id_id).id_telegram
                if instance.type == 'Rejected_registration':
                    bot.send_message(chat_id,
                                     f'Ваша заявка на регистрацию отменена по следующей причине: \n{instance.message_from_employee}')
                elif instance.type == 'Delete_profile':
                    bot.send_message(chat_id,
                                     f'Ваш аккаунт удален по следующей причине: \n{instance.message_from_employee}')
                elif instance.type == 'Rejected_booking':
                    event_canceled = event_status.get(id=instance.connection.event_id)
                    bot.send_message(chat_id,
                                     f'Ваша заявка на бронирование отклонена. По следующей причине: \n{instance.message_from_employee}' +
                                     booking['canceled'].format(
                                         event_canceled.name_event,
                                         room.get(id=event_canceled.room_id_id).name_room,
                                         event_canceled.quantity_people,
                                         datetime.strptime(str(event_canceled.date), '%Y-%m-%d').date().strftime(
                                             '%d.%m.%Y'),
                                         event_canceled.start_time,
                                         event_canceled.finish_time))
            elif instance.type == 'Other' and instance.message_id is not None:
                if instance.message_id is not None:
                    bot.send_message(instance.message_id,
                                     f'<b>Ранее вы отправляли вопрос:</b>\n{instance.message_from_user}\n\n<b>Ниже прилагаю ответ:</b>\n{instance.message_from_employee}')
            elif instance.type == 'Other' and instance.message_id is None:
                bot.send_message(User.objects.get(id=instance.user_id_id).id_telegram,
                                 f'<b>Сообщение сообщение от дичпетчера:</b>\n{instance.message_from_employee}')
            elif instance.type == 'Notification':
                for user_all in User.objects.filter(status='approval'):
                    chat_id = user_all.id_telegram
                    bot.send_message(chat_id, f'{instance.message_from_employee}')
            elif instance.type == 'Notification_company':
                for user_all in User.objects.filter(status='approval', type='company'):
                    chat_id = user_all.id_telegram
                    bot.send_message(chat_id, f'{instance.message_from_employee}')
            elif instance.type == 'Notification_private_person':
                for user_all in User.objects.filter(status='approval', type='private_person'):
                    chat_id = user_all.id_telegram
                    bot.send_message(chat_id, f'{instance.message_from_employee}')
    except Issue.DoesNotExist:
        return

@receiver(signals.post_save, sender=Coworking_Slot)
def auto_registration_slot(sender, instance, **kwargs):
    if Coworking_People.objects.filter(slot_id_id=instance.pk).exists() is False:
        user = User.objects.get(pk=instance.user_id_created_id)
        coworking_people = Coworking_People()
        coworking_people.slot_id_id = instance.pk
        coworking_people.full_name = f'{user.last_name} {user.first_name}'
        coworking_people.email = user.email
        coworking_people.phone = user.phone
        coworking_people.user_id_add_id = instance.user_id_created_id
        coworking_people.status_people = 'approval'
        coworking_people.visited = False
        coworking_people.save()
    else:
        return



# Изменение статуса мероприятия
if event_status.filter(status='approval') or event_status.filter(status='active'):
    if event_status.filter(date=datetime.now().date()):
        for element in event_status.filter(date=datetime.now().date()):
            if datetime.now().time() <= element.start_time < element.finish_time:
                element.status = 'active'
                element.save()
            elif element.finish_time <= datetime.now().time() and element.status == 'active':
                element.status = 'completed'
                element.save()

# web_hook_info = bot.get_webhook_info()
# logger.info('WebHookInfo: %s', web_hook_info)

# bot.remove_webhook()
# bot.set_webhook(url=WEBHOOK)
