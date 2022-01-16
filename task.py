from bot.views import bot
import logging

logger = logging.getLogger(__name__)
def send_event():
    try:
        bot.send_message(1217990186, 'Cron start')
    except Exception as e:
        logger.exception(e)

send_event()