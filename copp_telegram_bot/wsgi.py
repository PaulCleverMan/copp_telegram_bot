"""
WSGI config for copp_telegram_bot project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os, sys

#путь к проекту
sys.path.append('/home/p/pashok13ru/telegram_bot/public_html')
#путь к фреймворку
sys.path.append('/home/p/pashok13ru/telegram_bot')
#путь к виртуальному окружению
sys.path.append('/home/p/pashok13ru/.djangovenv/lib/python3.8/site-packages/')
#исключить системную директорию
sys.path.remove('/usr/lib/python3.8/site-packages')

os.environ["DJANGO_SETTINGS_MODULE"] = "copp_telegram_bot.settings"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()