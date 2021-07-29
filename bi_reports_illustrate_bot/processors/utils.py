from django_tgbot.decorators import processor
from django_tgbot.state_manager import message_types, update_types, state_types
from django_tgbot.types.replykeyboardmarkup import ReplyKeyboardMarkup
from django_tgbot.types.inlinekeyboardmarkup import InlineKeyboardMarkup
from django_tgbot.types.keyboardbutton import KeyboardButton
from django_tgbot.types.inlinekeyboardbutton import InlineKeyboardButton
from django_tgbot.types.update import Update
from django_tgbot.exceptions import ProcessFailure
from ..bot import state_manager
from ..models import TelegramState
from ..bot import TelegramBot
from ..bot import dv
from ..models import Report

from enum import Enum
import numpy as np


class MessageText(Enum):
    WEL = 'Hi {}, Welcome to the Report BI Bot. Click on Authorization button to authorize'
    SLG = 'You has been authorized by {} mobile number'    # Successful login
    REP = 'The {} field has been entered before! Please choose another field'   # Repetitive
    NFU = 'The field {} not found! Please chose a valid field'  # Not FoUnd
    UEX = 'An unexpected problem occurred! Try enter the fields from first again'
    CHP = 'Choose {}th parameter'
    CHT = 'Choose target'
    CTD = 'Click on download button for downloading the chart'
    INV = 'Invalid Choice '
    CNL = 'If you want to cancel the process, click on cancel button'


class ButtonText(Enum):
    CNL = 'Cancel'
    PAY = 'Payment'
    PIE = 'Pie Chart'
    GRP = 'Multi Group Chart'
    BAR = 'Bar Chart'
    LIN = 'Linear Chart'
    AUT = 'Authentication'
    DRW = 'Download'


# Commands
charts = {
    ButtonText.PIE.value: 2,
    ButtonText.GRP.value: 3,
    ButtonText.BAR.value: 2,
    ButtonText.LIN.value: 2
}


# Inline Buttons
# inline_pay_button = InlineKeyboardButton.a(text=ButtonText.PAY.value, callback_data=ButtonText.PAY.value)
# inline_pay_button.a(text='ali')

# inline_back_button = InlineKeyboardButton.a(text=ButtonText.CNL.value, callback_data=ButtonText.CNL.value)
# inline_switch_context = InlineKeyboardButton.a(text='alaki', switch_inline_query_current_chat='mohsen')

# Inline Keyboards
# select_cols_inline_keyboard = InlineKeyboardMarkup.a(inline_keyboard=[[inline_pay_button]])
input_params_keyboard = InlineKeyboardMarkup.a(inline_keyboard=[
    list(x) for x in np.array_split([InlineKeyboardButton.a(text=c, callback_data=c) for c in dv.get_all_fields()], dv.num_of_fields()/3)
])
# Reply Buttons


# Reply Keyboards
menu_keyboard = ReplyKeyboardMarkup.a(keyboard=[
    [
        KeyboardButton.a(text=ButtonText.PIE.value),
        KeyboardButton.a(text=ButtonText.LIN.value),
    ],
    [
        KeyboardButton.a(text=ButtonText.GRP.value),
        KeyboardButton.a(text=ButtonText.BAR.value),
    ]
], resize_keyboard=True)

auth_keyboard = ReplyKeyboardMarkup.a(keyboard=[
    [
        KeyboardButton.a(text=ButtonText.AUT.value, request_contact=True),
    ]
], resize_keyboard=True)

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