from django_tgbot.bot import AbstractTelegramBot
from django_tgbot.state_manager.state_manager import StateManager
from django_tgbot.types.update import Update
from django_tgbot.types.botcommand import BotCommand
from . import bot_token
from .models import TelegramUser, TelegramChat, TelegramState
from utils.core import DataVisualizer

import logging
logging.basicConfig(level='debug')


class TelegramBot(AbstractTelegramBot):
    def __init__(self, token, state_manager):
        super(TelegramBot, self).__init__(token, state_manager)

    def get_db_user(self, telegram_id):
        return TelegramUser.objects.get_or_create(telegram_id=telegram_id)[0]

    def get_db_chat(self, telegram_id):
        return TelegramChat.objects.get_or_create(telegram_id=telegram_id)[0]

    def get_db_state(self, db_user, db_chat):
        return TelegramState.objects.get_or_create(telegram_user=db_user, telegram_chat=db_chat)[0]

    def pre_processing(self, update: Update, user, db_user, chat, db_chat, state: TelegramState):
        super(TelegramBot, self).pre_processing(update, user, db_user, chat, db_chat, state)
        print(50 * '-')
        print(f'state memory is : {state.get_memory()}')
        print(f'state name is : {state.name}')
        try:
            from .processors.utils import ButtonText, menu_keyboard
            msg = update.get_message().get_text()
            if msg == '/reset':
                state.set_name('')
            elif msg == ButtonText.CNL.value:
                state.set_name('menu')
                bot.sendMessage(update.get_chat().get_id(), ButtonText.CNL.value, reply_markup=menu_keyboard)
            # elif msg == ButtonText.DRW.value:
            #     state.set_name('menu')
            #     bot.sendMessage(update.get_chat().get_id(), ButtonText.DRW.value, reply_markup=menu_keyboard)
        except Exception as e:
            print(str(e))

    def post_processing(self, update: Update, user, db_user, chat, db_chat, state: TelegramState):
        super(TelegramBot, self).post_processing(update, user, db_user, chat, db_chat, state)
        print(f'state memory is : {state.get_memory()}')
        print(f'state name is : {state.name}')
        print(50 * '-')

def import_processors():
    from . import processors


dv = DataVisualizer(rel_file_path='Financial Sample.xlsx')
state_manager = StateManager()
bot = TelegramBot(bot_token, state_manager)
bot.setMyCommands([BotCommand.a('reset', 'Restart Your Connection with Bot')])
import_processors()
