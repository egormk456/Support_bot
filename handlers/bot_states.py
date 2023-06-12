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