from .utils import *


@processor(state_manager, from_states=state_types.Reset, success='auth')
def welcome(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    try:
        # bot.sendMessage(chat_id, 'Hello!')
        res = MessageText.WEL.value.format(state.telegram_user.username)
        bot.sendMessage(chat_id, res, reply_markup=auth_keyboard)
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value, reply_markup=menu_keyboard)
        raise ProcessFailure


@processor(state_manager, from_states='auth', success='menu', fail=state_types.Reset)
def auth(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    try:
        mobile_number = f"{update.get_message().contact.phone_number}"
        # if mobile_number[0] != '+':
        #     mobile_number = '+' + mobile_number
        res = MessageText.SLG.value.format(mobile_number)
        bot.sendMessage(chat_id, res, reply_markup=menu_keyboard)
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value, reply_markup=menu_keyboard)
        raise ProcessFailure


@processor(state_manager, from_states='menu', message_types=message_types.Text)
def menu(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    try:
        msg = update.get_message().get_text()
        if msg == ButtonText.CNL.value:
            return
        assert msg in charts.keys(), MessageText.INV.value
        res = MessageText.CHP.value.format(1)
        msg_id = bot.sendMessage(chat_id, res, reply_markup=input_params_keyboard).get_message_id()
        # bot.sendMessage(chat_id, res, reply_markup=input_params_keyboard).get_message_id()
        bot.sendMessage(chat_id=chat_id, text=MessageText.CNL.value, reply_markup=cancel_keyboard)
        state.set_memory({
            'report': {
                'chart_name': msg,
                'chose_fields': []
            },
            'params_message_id': msg_id
        })
        state.set_name('input_params')
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value, reply_markup=menu_keyboard)
        raise ProcessFailure


@processor(state_manager, from_states='input_params', message_types=message_types.Text, fail='menu')
def input_params(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    try:
        if update.is_callback_query():
            callback_query = update.get_callback_query()
            chose = callback_query.get_data()
            print(chose)
            bot.answerCallbackQuery(callback_query_id=callback_query.get_id(), text="Received!")
        else:
            chose = update.get_message().get_text()

        # Check the selection is in columns
        if chose not in dv.get_all_fields():
            res = MessageText.NFU.value.format(chose)
            bot.sendMessage(chat_id, res)
            raise ProcessFailure

        # Get the report data until now
        report: dict = state.get_memory().get('report')

        # Calculate the remaining required params for drawing the diagram
        rem_params = charts.get(report.get('chart_name')) - len(report.get('chose_fields'))

        # Check we still need params
        assert rem_params != 0, MessageText.UEX.value

        # Check selected column is not repetitive
        if chose in report.get('chose_fields'):
            res = MessageText.REP.value.format(chose)
            bot.sendMessage(chat_id, res)
            return

        # Add Field to the stored fields
        report['chose_fields'].append(chose)

        # Update values
        state.update_memory({'report': report})
        rem_params -= 1

        # Send suitable message to user
        if rem_params == 0:
            state.set_name('draw')
            res = MessageText.CTD.value
            msg_id = state.get_memory().get('params_message_id')
            bot.deleteMessage(chat_id, msg_id)
            bot.sendMessage(chat_id, res, reply_markup=draw_keyboard)
        else:
            if rem_params == 1:
                res = MessageText.CHT.value
            else:
                res = MessageText.CHP.value.format(len(report.get('chose_fields')) + 1)
            msg_id = state.get_memory().get('params_message_id')
            # bot.sendMessage(chat_id=chat_id, text='I wanna reply :)', reply_to_message_id=msg_id)
            bot.editMessageText(text=res, chat_id=chat_id, message_id=msg_id, reply_markup=input_params_keyboard)
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value, reply_markup=menu_keyboard)
        raise ProcessFailure


@processor(state_manager, from_states='draw', success='menu', fail='menu')
def draw(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    try:
        # Get chart details
        report: dict = state.get_memory().get('report')
        params: list = report.get('chose_fields')
        chart: str = report.get('chart_name')

        # Drawing
        method_of_drawing = chart.lower().replace(' ', '_')
        full_path = dv.draw_and_save_fig(method_of_drawing, *params)
        if full_path:
            full_path = str(full_path)
            Report.objects.create(fig=full_path, params=params[:-1], target=params[-1])
            bot.sendDocument(chat_id, document=open(full_path, "rb"), upload=True, reply_markup=menu_keyboard)
        else:
            bot.sendMessage(chat_id, MessageText.UEX.value, reply_markup=menu_keyboard)

    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value, reply_markup=menu_keyboard)
        raise ProcessFailure
