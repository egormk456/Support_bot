from aiogram.dispatcher.filters.state import State, StatesGroup


class AddBotStates(StatesGroup):
    add_bot = State()