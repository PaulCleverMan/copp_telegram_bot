# /home/p/pashok13ru/.djangovenv/bin/python3.8 /home/p/pashok13ru/telegram_bot/public_html/manage.py task
from django.core.management.base import BaseCommand

# from bot import views

class Command(BaseCommand):
    help = 'The Zen of Python'

    def handle(self, *args, **options):
        import this
