from .utils import *


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
        # res = MessageText.SLG.value.format(mobile_number)
        res_text = states_data['auth_home']['msgs'][0]
        res_keyboard = keyboards[states_data['auth_home']['keyboards'][0]]
        bot.sendMessage(chat_id, res_text, reply_markup=res_keyboard)
        state_obj = state.get_memory()
        if state_obj.get('profile', None) is None:
            state.update_memory({
                'profile': {
                    'first_name': '',
                    'last_name': '',
                    'mobile_number': mobile_number
                }
            })
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value, reply_markup=auth_keyboard)
        raise ProcessFailure


@processor(state_manager, from_states='query_filter')
def filter_query(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    state_obj = state.get_memory()
    
    try:
        if update.is_callback_query():
            callback_query = update.get_callback_query()
            msg = callback_query.get_data()
            bot.answerCallbackQuery(callback_query_id=callback_query.get_id(), text="Received!")
        else:
            msg = update.get_message().get_text()
        
        if button_trans.get(msg, None):
            msg = button_trans[msg]
            
        if msg == ButtonText.FNS.value:
            next_state_name = state.name + '_run'
            go_to_state(bot, state, next_state_name)
            bot.sendMessage(chat_id,'choose:', reply_markup=chart_keyboards[state_obj.get('query')])
        else:
            query_obj = queries_data.get(state_obj.get('query'), None)
            filters = query_obj.get('filters', None)
            if msg in filters:
                next_state_name = state.name + '_adjust'
                filters = state_obj.get('filters', {})
                
                # TODO: the filter params for adjusment shoud be here
                filters[msg] = {}
                
                state_obj['filters'] = filters
                state.set_memory(state_obj)
                go_to_state(bot, state, next_state_name)
                bot.sendMessage(chat_id,'choose:', reply_markup=fake_inline_keyboard)
            
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value)
        # raise ProcessFailure


@processor(state_manager, from_states='query_filter_adjust')
def adjust_filter(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    state_obj = state.get_memory()
    
    try:
        if update.is_callback_query():
            callback_query = update.get_callback_query()
            msg = callback_query.get_data()
            bot.answerCallbackQuery(callback_query_id=callback_query.get_id(), text="Received!")
        else:
            msg = update.get_message().get_text()

        if button_trans.get(msg, None):
            msg = button_trans[msg]
            
        cur_filter = state_obj['filters'].keys()[-1]
        
        # go to run the query
        if msg == ButtonText.ACP.value:
            bot.sendMessage(chat_id, MessageText.FAD.value.format(cur_filter))
            go_to_prev_state(bot, state)
        elif msg == ButtonText.CNL.value:
            state_obj['filters'].pop(cur_filter)
            state.set_memory(state_obj)
            go_to_prev_state(bot, state)
            
        # TODO: write some code to get filter params and adjust filter        
        elif msg in ['test']:
            pass
        
        
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value)


@processor(state_manager, from_states='query_filter_run')
def run_query(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    state_obj = state.get_memory()
    
    try:
        if update.is_callback_query():
            callback_query = update.get_callback_query()
            msg = callback_query.get_data()
            bot.answerCallbackQuery(callback_query_id=callback_query.get_id(), text="Received!")
        else:
            msg = update.get_message().get_text()
        
        if button_trans.get(msg, None):
            msg = button_trans[msg]
        
        query_obj = queries_data.get(state_obj.get('query'))
        
        if msg in query_obj['charts']:  
            method_of_drawing = msg.lower().replace(' ', '_')
            full_path = dv.draw_and_save_fig(method_of_drawing, *query_obj['params'], query_obj['target'])
            if full_path:
                full_path = str(full_path)
                Report.objects.create(fig=full_path, params=query_obj['params'], target=query_obj['target'])
                bot.sendDocument(chat_id, document=open(full_path, "rb"), upload=True)
            else:
                bot.sendMessage(chat_id, MessageText.UEX.value)
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value)


code = ""
for state_name, data in states_data.items():
    query_list = ""
    if state_name in just_before_query_states:
        query_list="""res = bot.sendMessage(chat_id, next_state_message, reply_markup=query_keyboards[next_state_name])"""            
        
    if state_name in query_keyboards:
        # print("WE ARE IN QUERY KEYBOARDA!!!", flush=True)
        state_code = f"""query_obj = get_query_obj({state_name}, msg)
        if not query_obj:
            bot.sendMessage(chat_id, MessageText.PVC.value)
        else:
            state_obj = state.get_memory()
            state_obj.pop("filters", None)
            state_obj["state"] = "{state_name}"
            state_obj["query"] = msg
            state.set_memory(state_obj)
            go_to_state(bot, state, MEDIA_STATE)
            bot.sendMessage(chat_id, "choose:", reply_markup=filter_keybaords[msg])"""
    elif states_data[state_name].get('input', None):
        state_code= f"""set_vars_from_msg(state, "{states_data[state_name]['input']}", msg)
        go_to_prev_state(bot, state, MessageText.FSU.value)"""
    else:
        # print("WE AER IN ELSE!!!", flush=True)
        state_code = f"""next_state_name = "{state_name+'_'}" + msg
        next_state = states_data.get(next_state_name, None)
        if next_state is None:
            bot.sendMessage(chat_id, MessageText.PVC.value)
        else:
            go_to_state(bot,state, next_state_name)
            {query_list}"""
            
    code += f"""@processor(state_manager, from_states="{state_name}")
def {state_name}(bot, update, state):
    chat_id = update.get_chat().get_id()
    try:
        if update.is_callback_query():
            callback_query = update.get_callback_query()
            msg = callback_query.get_data()
            bot.answerCallbackQuery(callback_query_id=callback_query.get_id(), text="Received!")
        else:
            msg = update.get_message().get_text()
        if button_trans.get(msg, None):
            msg = button_trans[msg]
        if msg in ["back", "home"]:
            return
        {state_code}

    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value)
        raise ProcessFailure\n\n\n"""
re.sub('\n\t', '\n', code)
# print(code)
exec(code)
