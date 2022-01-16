import os
import sys

sys.path.append('/home/p/pashok13ru/telegram_bot/public_html/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'copp_telegram_bot.settings'

from bot import views

def send_event():
    try:
        views.bot.send_message(1217990186, 'Cron start')
    except Exception as e:
        print(e)

if __name__ == "__main__":
    send_event()
    print('Work')
