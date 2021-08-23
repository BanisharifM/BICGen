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
    FSU = 'The field has been updated successfully!'
    CFT = 'Choose a filter'
    FAD = 'Filter {} added successfully!'


class ButtonText(Enum):
    CNL = 'Cancel'
    PAY = 'Payment'
    PIE = 'Pie Chart'
    GRP = 'Multi Group Chart'
    BAR = 'Bar Chart'
    LIN = 'Linear Chart'
    AUT = 'Authentication'
    DRW = 'Download'
    FNS = 'ّFinish'
    ACP = 'Accept'
    


# Commands
charts = {
    ButtonText.PIE.value: 2,
    ButtonText.GRP.value: 3,
    ButtonText.BAR.value: 2,
    ButtonText.LIN.value: 2
}

MEDIA_STATE = 'query_filter'

buttons_data = json.load(open(settings.BASE_DIR/"bi_reports_illustrate_bot/data/buttons.json"))
keyboards_data: dict = json.load(open(settings.BASE_DIR/"bi_reports_illustrate_bot/data/keyboards.json"))
states_data = json.load(open(settings.BASE_DIR/"bi_reports_illustrate_bot/data/states.json"))
queries_data = json.load(open(settings.BASE_DIR/"bi_reports_illustrate_bot/data/queries.json"))


# inline_pay_button = InlineKeyboardButton.a(text=ButtonText.PAY.value, callback_data=ButtonText.PAY.value)
# inline_pay_button.a(text='ali')

# inline_back_button = InlineKeyboardButton.a(text=ButtonText.CNL.value, callback_data=ButtonText.CNL.value)
# inline_switch_context = InlineKeyboardButton.a(text='alaki', switch_inline_query_current_chat='mohsen')

# select_cols_inline_keyboard = InlineKeyboardMarkup.a(inline_keyboard=[[inline_pay_button]])
# input_params_keyboard = InlineKeyboardMarkup.a(inline_keyboard=[
#     list(x) for x in np.array_split([InlineKeyboardButton.a(text=c, callback_data=c) for c in dv.get_all_fields()],
#                                     dv.num_of_fields() / 3)
# ])


# menu_keyboard = ReplyKeyboardMarkup.a(keyboard=[
#     [
#         KeyboardButton.a(text=ButtonText.PIE.value),
#         KeyboardButton.a(text=ButtonText.LIN.value),
#     ],
#     [
#         KeyboardButton.a(text=ButtonText.GRP.value),
#         KeyboardButton.a(text=ButtonText.BAR.value),
#     ]
# ], resize_keyboard=True)

# auth_keyboard = ReplyKeyboardMarkup.a(keyboard=[
#     [
#         KeyboardButton.a(text=ButtonText.AUT.value, request_contact=True),
#     ]
# ], resize_keyboard=True)


# def get_valid_query_names(state_name: str):
#     try:
#         return states_data[state_name]['queries']
#     except:
#         return []


# def get_query_obj(state_name: str, query_name: str):
#     try:
#         return states_data[state_name]['queries']
#         data = states_data.get(state_name, None)
#         if data:
#             state_queries = data.get('queries', None)
#             if state_queries and query_name in state_queries:
#                 return queries_data.get(query_name, None)
#         return None


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
    trim_var = var[1:-1]
    parts = trim_var.split('.')
    state_obj = state.get_memory()[parts[0]]
    if len(parts) == 2:
        state_obj[parts[1]] = res
    elif len(parts) == 1:
        state_obj = res
    state.update_memory({parts[0]: state_obj})
    
    
def go_to_prev_state(bot, state: TelegramState, msg=None):    
    if state.name == MEDIA_STATE:
        state_obj = state.get_memory()
        state_obj.pop('query', None)
        state_obj.pop('filters', None)
        next_state_name = state_obj.pop('state', 'auth_home')
        state.set_memory(state_obj)
    else:        
        next_state_name =  re.sub('(.*)_.*', r'\1', state.name)
    go_to_state(bot, state, next_state_name)    
    
    
def go_to_state(bot: TelegramBot, state: TelegramState, state_name: str, msg=None):
    chat_id = state.telegram_chat.telegram_id
    state.set_name(state_name)
    msg = msg if msg else states_data[state_name]['msgs'][0]
    msg = message_trans(state, msg)
    keyboard = get_keyboard_of_state(state_name=state_name)
    bot.sendMessage(chat_id, msg, reply_markup=keyboard)


def get_keyboard_of_state(state_name: str):
    return keyboards[states_data[state_name]['keyboards'][0]]
    
    
def register_static_data():
    static_buttons = {
        "finish": {
            "text": ButtonText.FNS.value
        },
        "accept": {
            "text": ButtonText.ACP.value
        },
        "cancel": {
            "text": ButtonText.CNL.value
        },
        "Pie Chart": {
            "text": "Pie Chart"
        },
        "Multi Group Chart": {
            "text": "Multi Group Chart"
        },
        "Bar Chart": {
            "text": "Bar Chart"
        },
        "Linear Chart": {
            "text": "Linear Chart"
        },
        
    }
    static_keyboards = {
        "filter": {
            "type": "reply",
            "buttons": [
                [
                    "finish"
                ],
                [
                    "home",
                    "back"
                ]
            ]
        },
        "adjustFilter": {
            "type": "reply",
            "buttons": [
                [
                    "cancel",
                    "accept"
                ]
            ]
        },     
    }
    static_states = {
        "query_filter": {
            "keyboards": [
                "filter"
            ],
            "msgs": [
                "Please select a filter to apply."
            ]
        },
        "query_filter_adjust": {
            "keyboards": [
                "adjustFilter"
            ],
            "msgs": [
                "Adjust the filter"
            ]
        },
        "query_filter_run": {
            "keyboards": [
                "back_and_home"
            ],
            "msgs": [
                "The drawing is in process..."
            ]
        }
    }
    buttons_data.update(static_buttons)
    keyboards_data.update(static_keyboards)
    states_data.update(static_states)
    
    
# add static data to user data
register_static_data()

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
query_keyboards = dict() # key: state_name, value: queries of this state as in an inline keyboard
filter_keybaords = dict() # key: query_name, value: filters of this query as in an inline keyboards
chart_keyboards = dict() # key: query_name, value: allowed charts of this query as inline keyboards

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
            if query_name not in filter_keybaords:
                filter_keyboard_inline_buttons = list()
                for filt in queries_data[query_name]['filters']:
                    filter_keyboard_inline_buttons.append([
                        InlineKeyboardButton.a(text=filt,
                            callback_data=filt
                        )      
                    ])
                filter_keybaords[query_name] = InlineKeyboardMarkup.a(filter_keyboard_inline_buttons)

            if query_name not in chart_keyboards:
                chart_keyboard_inline_buttons = list()
                for chart in queries_data[query_name]['charts']:
                    chart_keyboard_inline_buttons.append([
                        InlineKeyboardButton.a(text=chart,
                            callback_data=chart
                        )
                    ])
                chart_keyboards[query_name] = InlineKeyboardMarkup.a(chart_keyboard_inline_buttons)
        query_keyboards[st_name] = InlineKeyboardMarkup.a(query_keyboard_inline_buttons)

just_before_query_states = [re.sub('(.*)_.*', r'\1', qkb) for qkb in query_keyboards]


