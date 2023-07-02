from aiogram.dispatcher.filters.state import State, StatesGroup


class BotStates(StatesGroup):
    mailing = State()
    usual_state = State()

    add_command = State()
    add_description = State()

    choose_command = State()
    edit_text_command = State()
    delete_command = State()

    edit_start_message = State()


class AddBotStates(StatesGroup):
    add_bot = State()


class FunnelStates(StatesGroup):
    add_funnel = State()
    add_step = State()
    add_time = State()
    add_trigger = State()
    steps_list = State()
    funnel_steps = State()