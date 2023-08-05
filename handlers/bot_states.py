from aiogram.dispatcher.filters.state import State, StatesGroup


class BotStates(StatesGroup):
    admin_mailing_all_users = State()
    admin_mailing_to_admins = State()
    add_invite_link = State()
    invites_links = State()

    bot_settings = State()
    bot_list = State()
    mailing = State()
    delete_bot = State()
    usual_state = State()

    add_command = State()
    add_description = State()
    edit_command = State()

    choose_command = State()
    edit_text_command = State()
    delete_command = State()

    edit_start_message = State()
    add_markup = State()
    add_application = State()
    add_application_name = State()


class AddBotStates(StatesGroup):
    add_bot = State()
    step_1 = State()
    step_2 = State()


class FunnelStates(StatesGroup):
    add_funnel = State()
    add_step = State()
    add_time = State()
    add_trigger = State()
    steps_list = State()
    funnel_steps = State()
    delete_step = State()

