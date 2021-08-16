from django_tgbot.bot import AbstractTelegramBot
from django_tgbot.state_manager.state_manager import StateManager
from django_tgbot.types.update import Update
from django_tgbot.types.botcommand import BotCommand
from . import bot_token
from .models import TelegramUser, TelegramChat, TelegramState
from utils.core import DataVisualizer

import logging
logging.basicConfig(level='DEBUG')


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
        chat_id = update.get_chat().get_id()
        super(TelegramBot, self).pre_processing(update, user, db_user, chat, db_chat, state)
        # bot.sendMessage(chat_id, f'state memory is : {state.get_memory()}')
        # bot.sendMessage(chat_id, f'state name is : {state.name}')
        print(50 * '-')
        # print(f'state memory is : {state.get_memory()}')
        print(f'state name is : {state.name}')
        print(flush=True)
        # bot.sendMessage(, 'developer test')
        from bi_reports_illustrate_bot.processors.auto import keyboards, states_data, button_trans
        import re
        
        try:
            from .processors.utils import ButtonText, menu_keyboard
            msg = update.get_message().get_text()
            if button_trans.get(msg, None):
                msg = button_trans[msg]
            if msg in ['/reset', '/start']:
                state.set_name('')
            elif msg in ['back', 'home']:
                next_state_name = 'auth_home' if msg == 'home' else re.sub('(.*)_.*', r'\1', state.name)
                state.set_name(next_state_name)
                keyboard_name = states_data[next_state_name]['keyboards'][0]
                next_state_keyboard = keyboards[keyboard_name]
                bot.sendMessage(chat_id, msg, reply_markup=next_state_keyboard)
            elif msg == ButtonText.CNL.value:
                state.set_name('menu')
                bot.sendMessage(update.get_chat().get_id(), ButtonText.CNL.value, reply_markup=menu_keyboard)
                memory_state = state.get_memory()
                msg_id = memory_state.pop('params_message_id', None)
                if msg_id is not None:
                    bot.deleteMessage(update.get_chat().get_id(), msg_id)
                    state.set_memory(memory_state)
        except Exception as e:
            print(str(e))

    def post_processing(self, update: Update, user, db_user, chat, db_chat, state: TelegramState):
        super(TelegramBot, self).post_processing(update, user, db_user, chat, db_chat, state)
        # print(f'state memory is : {state.get_memory()}')
        print(f'state name is : {state.name}')
        print(50 * '-')
        print(flush=True)
        chat_id = update.get_chat().get_id()
        # bot.sendMessage(chat_id, f'state memory is : {state.get_memory()}')
        # bot.sendMessage(chat_id, f'state name is : {state.name}')


def import_processors():
    from . import processors


dv = DataVisualizer(rel_file_path='Financial Sample.xlsx')
state_manager = StateManager()
bot = TelegramBot(bot_token, state_manager)
bot.setMyCommands([BotCommand.a('restart', 'Restart The Bot'), BotCommand.a('start', 'Start The Bot')])
import_processors()
