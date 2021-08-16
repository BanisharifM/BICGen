from .utils import *

import json
import re

buttons_data = json.load(open("../data/buttons.json"))
keyboards_data: dict = json.load(open("../data/keyboards.json"))
states_data = json.load(open("../data/states.json"))
queries_data = json.load(open("../data/queries.json"))

# create keyboards
keyboards = dict()
for kb_name, data in keyboards_data:
    if data['type'] == 'inline':
        keyboards[kb_name] = InlineKeyboardMarkup.a(
            [[InlineKeyboardButton.a(
                text=buttons_data[btn]['text']) for btn in btn_list] for btn_list in data["buttons"]]
        )
    elif data['type'] == 'reply':
        keyboards[kb_name] = ReplyKeyboardMarkup.a(
            [[KeyboardButton.a(
                text=buttons_data[btn]['text']) for btn in btn_list] for btn_list in data["buttons"]],
            resize_keyboard=True
        )

auth_keyboard = ReplyKeyboardMarkup.a(keyboard=[
    [
        KeyboardButton.a(text=buttons_data['auth']['text'], request_contact=True),
    ]
], resize_keyboard=True)

# create inline query keyboards
query_keyboards = dict()
for st_name, data in states_data:
    queries = data.get('queries', None)
    if queries:
        query_keyboards[st_name] = InlineKeyboardMarkup.a(
            [[InlineKeyboardButton.a(
                text=queries_data[query_name]['text'])] for query_name in queries]
        )

just_before_query_states = [re.sub('(.*)_.*', r'\1', qkb) for qkb in query_keyboards]


@processor(state_manager, from_states=state_types.Reset, success='auth')
def welcome(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    try:
        res = MessageText.WEL.value.format(state.telegram_user.username)
        bot.sendMessage(chat_id, res, reply_markup=auth_keyboard)
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value)
        raise ProcessFailure


@processor(state_manager, from_states='auth', success='auth_home', fail=state_types.Reset)
def auth(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    try:
        mobile_number = f"{update.get_message().contact.phone_number}"
        # if mobile_number[0] != '+':
        #     mobile_number = '+' + mobile_number
        res = MessageText.SLG.value.format(mobile_number)
        bot.sendMessage(chat_id, res, reply_markup=keyboards['home'])
        state_obj = state.get_memory()
        if state_obj.get('profile', None) is None:
            state_obj.update({
                'profile': {
                    'first_name': '',
                    'last_name': ''
                }
            })
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value, reply_markup=auth_keyboard)
        raise ProcessFailure


@processor(state_manager, from_states='run_query')
def run_query(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    try:
        if update.is_callback_query():
            callback_query = update.get_callback_query()
            msg = callback_query.get_data()
            bot.answerCallbackQuery(callback_query_id=callback_query.get_id(), text="Received!")
        else:
            msg = update.get_message().get_text()
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value)
        # raise ProcessFailure


nl = '\n'
code = ""
for state_name, data in states_data:
    if state_name in query_keyboards:
        state_code = f"""\
                bot.sendMessage(chat_id, "in process")
                state.set_name("run_query")
                state_obj = state.get_memory()
                state_obj.update({{"state": {state_name}}})"""
    else:
        state_code = f"""\
                next_state_name = {state_name+'_'}+msg
                next_state = states_data.get(next_state_name, None)
                if next_state is None:
                    bot.sendMessage(chat_id, MessageText.UEX.value)
                else:
                    state.set_name(next_state)
                    next_state_keyboard_name = next_state['keyboards'][0]
                    next_state_keyboard = keyboards[next_state_keyboard_name]
                    next_state_message = next_state[msgs][0]
                    bot.sendMessage(chat_id, next_state_message, next_state_keyboard)
                    {'bot.sendMessage(chat_id, next_state_message, query_keyboards[next_state_name])'
                    if state_name in just_before_query_states else ''}"""
    code += f"""\
    @processor(state_manager, from_states={state_name})
    def {state_name}(bot, update, state):
        chat_id = update.get_chat().get_id()
        try:
            if update.is_callback_query():
                callback_query = update.get_callback_query()
                msg = callback_query.get_data()
                bot.answerCallbackQuery(callback_query_id=callback_query.get_id(), text="Received!")
            else:
                msg = update.get_message().get_text()
                {state_code}

        except Exception as e:
            print(str(e))
            bot.sendMessage(chat_id, MessageText.UEX.value)
            raise ProcessFailure
    """
print(code)
exec(code)
