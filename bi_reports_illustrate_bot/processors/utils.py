from django_tgbot.decorators import processor
from django_tgbot.state_manager import message_types, update_types, state_types
from django_tgbot.types import inlinekeyboardbutton
from django_tgbot.types.replykeyboardmarkup import ReplyKeyboardMarkup
from django_tgbot.types.inlinekeyboardmarkup import InlineKeyboardMarkup
from django_tgbot.types.keyboardbutton import KeyboardButton
from django_tgbot.types.inlinekeyboardbutton import InlineKeyboardButton
from django_tgbot.types.update import Update
from django_tgbot.exceptions import ProcessFailure
from django.conf import settings

from ..bot import state_manager
from ..models import TelegramState
from ..bot import TelegramBot
from ..bot import dv
from ..models import Report

from enum import Enum
import numpy as np
import json
import re


class MessageText(Enum):
    WEL = 'Hi {},  Welcome to the CBIC.\nIf you are sure you are registered in the bot, click the “Authenticate”.\nOtherwise, contact to admin.'
    SLG = 'You has been authorized by {} mobile number'  # Successful login
    REP = 'The {} field has been entered before! Please choose another field'  # Repetitive
    NFU = 'The field {} not found! Please chose a valid field'  # Not FoUnd
    UEX = 'An unexpected problem occurred! Try enter the fields from first again'
    CHP = 'Choose {}th parameter'
    CHT = 'Choose target'
    CTD = 'Click on download button for downloading the chart'
    INV = 'Invalid Choice '
    CNL = 'If you want to cancel the process, click on cancel button'
    PVC = 'Please Enter a valid choice'
    FSU = 'The field registered'
    CFT = 'Choose a filter'
    FAD = 'Filter {} added successfully!'
    CHS = 'Choose'


class ButtonText(Enum):
    PAY = 'Payment'
    PIE = 'Pie Chart'
    GRP = 'Multi Group Chart'
    BAR = 'Bar Chart'
    LIN = 'Linear Chart'
    AUT = 'Authentication'
    DRW = 'Download'
    FNS = 'ّFinish'
    ACP = 'Accept'
    CNL = 'Cancel'
    


# Commands
charts = {
    ButtonText.PIE.value: 2,
    ButtonText.GRP.value: 3,
    ButtonText.BAR.value: 2,
    ButtonText.LIN.value: 2
}

MEDIA_STATE = 'query_filter'

buttons_dynamic_data = json.load(open(settings.BASE_DIR/"bi_reports_illustrate_bot/data/buttons.json"))
keyboards_dynamic_data = json.load(open(settings.BASE_DIR/"bi_reports_illustrate_bot/data/keyboards.json"))
states_dynamic_data = json.load(open(settings.BASE_DIR/"bi_reports_illustrate_bot/data/states.json"))
queries_dynamic_data = json.load(open(settings.BASE_DIR/"bi_reports_illustrate_bot/data/queries.json"))

buttons_static_data = json.load(open(settings.BASE_DIR/"bi_reports_illustrate_bot/static_data/buttons.json"))
keyboards_static_data = json.load(open(settings.BASE_DIR/"bi_reports_illustrate_bot/static_data/keyboards.json"))
states_static_data = json.load(open(settings.BASE_DIR/"bi_reports_illustrate_bot/static_data/states.json"))
# queries_static_data = json.load(open(settings.BASE_DIR/"bi_reports_illustrate_bot/static_data/queries.json"))

# merge dynamic and static data
buttons_data, keyboards_data, states_data, queries_data = [{}, {}, {}, {}]

buttons_data.update(buttons_static_data)
buttons_data.update(buttons_dynamic_data)

keyboards_data.update(keyboards_static_data)
keyboards_data.update(keyboards_dynamic_data)

states_data.update(states_static_data)
states_data.update(states_dynamic_data)

queries_data.update(queries_dynamic_data)


def message_trans(state: TelegramState, msg: str):
    vars = re.findall('\{.*?\}', msg)
    for var in vars:
        trim_var = var[1:-1]
        parts = trim_var.split('.')
        state_obj = state.get_memory()
        result = state_obj
        for part in parts:
            result = result.get(part, None)
            if result is None:
                return None
        msg = msg.replace(var, result)
        print(msg)
    print(msg, flush=True)
    return msg


def set_vars_from_msg(state: TelegramState, var: str, res: str):
    is_list = False
    if var[0] == '+':
        is_list = True
        var = var[1:]
    trim_var = var[1:-1]
    parts = trim_var.split('.')
    
    if len(parts) == 2:
        state_obj = state.get_memory().get(parts[0], {})
        if is_list:
            state_obj[parts[1]].append(res)
        else:
            state_obj[parts[1]] = res
        state.update_memory({parts[0]: state_obj})
    elif len(parts) == 1:
        if is_list:
            res = state.get_memory().get(parts[0], []).append(res)
        state.update_memory({parts[0]: res})
        
    
    
def go_to_prev_state(bot, state: TelegramState, msg=None):  
    state_obj = state.get_memory()
    if state_obj.get("states", None):
        state_obj["states"].pop(-1)
        state.set_memory(state_obj)
    if state.name == MEDIA_STATE:
        next_state_name = state_obj["states"][0]
    else:        
        next_state_name =  re.sub('(.*)_.*', r'\1', state.name)
    go_to_state(bot, state, next_state_name)
    
    
def go_to_state(bot: TelegramBot, state: TelegramState, state_name: str, msg=None):
    chat_id = state.telegram_chat.telegram_id
    state_obj = state.get_memory()
    
    state.set_name(state_name)
    msg = msg if msg else states_data[state_name]['msgs'][0]
    msg = message_trans(state, msg)
    reply_keyboard = get_reply_keyboard_of_state(state_name)
    bot.sendMessage(chat_id, msg, reply_markup=reply_keyboard)
    
    if state_obj.get('states', None):
        inline_keyboard = get_inline_keyboard_of_state(state_obj['states'][-1])
        bot.sendMessage(chat_id, MessageText.CHS.value, reply_markup=inline_keyboard)


def get_reply_keyboard_of_state(state_name: str):
    try:
        return keyboards[states_data[state_name]['keyboards'][0]]
    except:
        return None


def get_inline_keyboard_of_state(state_name: str):
    return inline_keyboards.get(state_name, None)
    

# buttons translator
button_trans = {v['text']: k for k,v in buttons_data.items()}

# create keyboards
keyboards = dict()
for kb_name, data in keyboards_data.items():
    if data['type'] == 'inline':
        keyboards[kb_name] = InlineKeyboardMarkup.a(
            [[InlineKeyboardButton.a(
                text=buttons_data[btn]['text'], callback_data=buttons_data[btn]['text']) for btn in btn_list] for btn_list in data["buttons"]]
        )
    elif data['type'] == 'reply':
        keyboards[kb_name] = ReplyKeyboardMarkup.a(
            [[KeyboardButton.a(
                text=buttons_data[btn]['text']) for btn in btn_list] for btn_list in data["buttons"]],
            resize_keyboard=True
        )

# KEYBOARDS        
cancel_keyboard = ReplyKeyboardMarkup.a(keyboard=[
    [
        KeyboardButton.a(text=ButtonText.CNL.value),
    ]
], resize_keyboard=True)

draw_keyboard = ReplyKeyboardMarkup.a(keyboard=[
    [
        KeyboardButton.a(text=ButtonText.DRW.value),
    ]
], resize_keyboard=True)

finish_keyboard = ReplyKeyboardMarkup.a(keyboard=[
    [
        KeyboardButton.a(text=buttons_data['back']['text']),
        KeyboardButton.a(text=ButtonText.FNS.value),
    ]
], resize_keyboard=True)

auth_keyboard = ReplyKeyboardMarkup.a(keyboard=[
    [
        KeyboardButton.a(text=buttons_data['auth']['text'], request_contact=True),
    ]
], resize_keyboard=True)

fake_inline_keyboard = InlineKeyboardMarkup.a([[InlineKeyboardButton.a(text='test', callback_data='test')]])

# create inline query keyboards
inline_keyboards = dict()

for st_name, data in states_data.items():
    queries = data.get('queries', None)
    if queries:
        query_keyboard_inline_buttons = list()
        for query_name in queries:
            query_keyboard_inline_buttons.append([
                InlineKeyboardButton.a(text=queries_data[query_name]['text'],
                    callback_data=query_name
                )      
            ])
            if "query_filter_"+query_name not in inline_keyboards:
                filter_keyboard_inline_buttons = list()
                for filt in queries_data[query_name]['filters']:
                    filter_keyboard_inline_buttons.append([
                        InlineKeyboardButton.a(text=filt,
                            callback_data=filt
                        )      
                    ])
                    if "query_filter_adjust_"+filt not in inline_keyboards:
                        adj_filter_keyboard_inline_buttons = list()
                        adj_filter_keyboard_inline_buttons.append([
                            InlineKeyboardButton.a(text='test',
                                callback_data='test'
                            )
                        ])
                        inline_keyboards["query_filter_adjust_"+filt] = InlineKeyboardMarkup.a(adj_filter_keyboard_inline_buttons)
                inline_keyboards["query_filter_"+query_name] = InlineKeyboardMarkup.a(filter_keyboard_inline_buttons)

            if "query_filter_run_"+query_name not in inline_keyboards:
                chart_keyboard_inline_buttons = list()
                for chart in queries_data[query_name]['charts']:
                    chart_keyboard_inline_buttons.append([
                        InlineKeyboardButton.a(text=chart,
                            callback_data=chart
                        )
                    ])
                inline_keyboards["query_filter_run_" + query_name] = InlineKeyboardMarkup.a(chart_keyboard_inline_buttons)
        inline_keyboards[st_name] = InlineKeyboardMarkup.a(query_keyboard_inline_buttons)
