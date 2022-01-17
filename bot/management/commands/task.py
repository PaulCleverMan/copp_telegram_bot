# /home/p/pashok13ru/.djangovenv/bin/python3.8 /home/p/pashok13ru/telegram_bot/public_html/manage.py task
from django.core.management.base import BaseCommand

from bot import views

class Command(BaseCommand):

    def handle(self, *args, **options):
        for chat_id in range(len(views.group_chats_access)):
            views.send_event(views.group_chats_access[chat_id])
        return
