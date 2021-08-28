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
            state.set_memory({
                'profile': {
                    'first_name': '',
                    'last_name': '',
                    'mobile_number': mobile_number
                }
            })
        else:
            state.set_memory({
               'profile': state_obj['profile']
            })
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value, reply_markup=auth_keyboard)
        raise ProcessFailure

@processor(state_manager, from_states='auth_home_reportsList')
def report_list(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    
    try:
        msg = get_message_from_update(bot, update)

        if msg in ["back", "home"]:
            return
        
        if msg in ["next", "prev"]:
            update_reports_list_config(state, msg)
            state_obj = state.get_memory()
            msg_id = state_obj["last_inline_message_id"]
            kb_name = state_obj["reportsKeyboardName"]
            kb = keyboards[kb_name]
            bot.editMessageText(text=get_reports_list(state), chat_id=chat_id, message_id=msg_id, reply_markup=kb, parse_mode="MarkdownV2")
        else:
            bot.sendMessage(chat_id, MessageText.PVC.value)
        
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value)
    

@processor(state_manager, from_states='query_filter')
def filter_query(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    state_obj = state.get_memory()
    
    try:
        msg = get_message_from_update(bot, update)
        
        if msg in ["back", "home"]:
            return
        
        if msg == "finish":
            next_state_name = state.name + '_run'
            state_obj.setdefault("states", []).append(next_state_name + "_" + state_obj["query"])
            state.set_memory(state_obj)
            go_to_state(bot, state, next_state_name)
        else:
            query_obj = queries_data.get(state_obj["query"], None)
            if msg not in query_obj["filters"]:
                bot.sendMessage(chat_id, MessageText.PVC.value)
            else:
                next_state_name = state.name + '_adjust'
                state_obj.setdefault("states", []).append(next_state_name + "_" + msg)
                filters = state_obj.get('filters', {})
                
                # TODO: the filter params for adjusment shoud be here
                filters[msg] = {}
                
                state_obj['filters'] = filters
                state.set_memory(state_obj)
                go_to_state(bot, state, next_state_name)
            
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value)


@processor(state_manager, from_states='query_filter_adjust')
def adjust_filter(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    state_obj = state.get_memory()
    
    try:
        msg = get_message_from_update(bot, update)
            
        if msg in ["back", "home"]:
            return
        
        cur_filter = list(state_obj['filters'].keys())[-1]
        
        print(f"message is {msg}")
        # go to run the query
        if msg == "accept":
            bot.sendMessage(chat_id, MessageText.FAD.value.format(cur_filter))
            go_to_prev_state(bot, state)
        elif msg == "cancel":
            state_obj['filters'].pop(cur_filter, None)
            state.set_memory(state_obj)
            go_to_prev_state(bot, state)
            
        # TODO: write some code to get filter params and adjust filter        
        elif msg in ['test']:
            print("you hit some filter adjusment")
        
        
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value)


@processor(state_manager, from_states='query_filter_run')
def run_query(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    state_obj = state.get_memory()
    
    try:
        msg = get_message_from_update(bot, update)
        
        query_obj = queries_data.get(state_obj.get('query'))
        
        if msg in query_obj['charts']:
            method_of_drawing = msg.lower().replace(' ', '_')
            rel_path = dv.draw_and_save_fig(method_of_drawing, *query_obj['params'], query_obj['target'])
            if rel_path:
                rel_path = str(rel_path)
                report_name = query_obj['target'] + ' by ' + ' and '.join(query_obj['params']) + '_' + msg
                r = Report.objects.create(name=report_name, owner=state.telegram_user, fig=rel_path, params=query_obj['params'], target=query_obj['target'])
                bot.sendDocument(chat_id, document=open(r.fig.path, "rb"), upload=True)
            else:
                bot.sendMessage(chat_id, MessageText.UEX.value)
    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value)


code = ""
for state_name, data in states_dynamic_data.items():        
    # handle input
    handle_input=""
    if states_data[state_name].get('input', None):
        handle_input= f"""set_vars_from_msg(state, "{data['input']}", msg)
        state_obj = state.get_memory()"""
    
    # handle state    
    if data.get('queries', None):
        handle_state = f"""next_state_name = MEDIA_STATE + "_" + msg
        if next_state_name in inline_keyboards:
            state_obj["filters"] = dict()
            state_obj.setdefault("states", []).append(next_state_name)
            next_state_name = MEDIA_STATE
        else:
            bot.sendMessage(chat_id, MessageText.PVC.value)
            return"""
    elif data.get('jump', None):
        handle_state = f"""next_state_name = "{data['jump']}" """
    else:
        handle_state = f"""next_state_name = "{state_name+'_'}" + msg"""
    
    # handle output
    handle_output = f"""if next_state_name not in states_data:
            bot.sendMessage(chat_id, MessageText.PVC.value)
            return
        if next_state_name in inline_keyboards:
            state_obj.setdefault("states", []).append(next_state_name)
        state.set_memory(state_obj)
        go_to_state(bot, state, next_state_name)"""
    
    code += f"""\
@processor(state_manager, from_states="{state_name}")
def {state_name}(bot, update, state):
    chat_id = update.get_chat().get_id()
    state_obj = state.get_memory()
    
    try:
        msg = get_message_from_update(bot, update)
        
        if msg in ["back", "home"]:
            return
        
            
        {handle_input}
        {handle_state}
        {handle_output}

    except Exception as e:
        print(str(e))
        bot.sendMessage(chat_id, MessageText.UEX.value)
        raise ProcessFailure\n\n\n"""
re.sub('\n\t', '\n', code)
exec(code)
