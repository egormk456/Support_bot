from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from utils.db_api.database import Database
from utils.db_api.funnel_db import FunnelDatabase
from utils.usefull_functions.sending_message import sending_function
from utils.usefull_functions.create_markup import create_markup

import asyncio
used_tokens = []


async def funnel_mailing():
    db = Database("comments.db")
    funnel_db = FunnelDatabase("funnels.db")

    now_day = datetime.now().day
    tokens = db.get_tokens()

    if tokens is not None:
        for token in tokens:
            bot = Bot(token=token)
            chat_id = db.get_chat_link(bot_token=token)
            group_id = db.get_group_id(bot_token=token)
            funnel_users = funnel_db.get_users(token=token)
            funnel_users = [user[0] for user in funnel_users]

            for user in funnel_users:
                user_step_number, user_trigger_time = funnel_db.get_user_step_number_and_time(tg_id=user, token=token)
                steps_info = funnel_db.get_steps_info(token=token)
                user_trigger_minutes, user_trigger_day = user_trigger_time.split(" ")

                if steps_info is not None:
                    for step, minutes, step_number, audio, photo, video, video_note, document, document_name, markup_text, application_text, application_button, application_name in steps_info:
                        user_trigger_minutes = int(user_trigger_minutes)
                        user_trigger_day = int(user_trigger_day)

                        now_minutes = datetime.now().hour * 60 + datetime.now().minute
                        tt = user_trigger_minutes + minutes
                        if tt >= 1440:
                            tt = tt - 1440
                            user_trigger_day += 1


                        # print(f"{tt =}, {now_minutes=}, {user_trigger_day =}, {now_day =}, {step_number =}, {user_step_number =}, {token =}")
                        if (tt <= now_minutes and user_trigger_day <= now_day and step_number == user_step_number):
                                # or (now_day <= user_trigger_day and step_number == user_step_number):

                            markup = InlineKeyboardMarkup()

                            if application_button is None:
                                application_button = "Оставить заявку"

                            if application_name is not None:
                                markup.add(
                                    InlineKeyboardButton(
                                        text=application_button, callback_data=application_name
                                    )
                                )

                            commands_list = db.get_commands_list(bot_token=token)
                            if markup_text != "0":
                                markup = create_markup(markup_text=markup_text, markup=markup, commands_list=commands_list)

                            funnel_message = await sending_function(
                                bot=bot,
                                chat_id=user,
                                text=step,
                                audio=audio,
                                photo=photo,
                                video=video,
                                video_note=video_note,
                                document=document,
                                document_name=document_name,
                                markup=markup
                            )

                            try:
                                db.add_user_message(
                                    tg_id=user,
                                    message_id=funnel_message.message_id,
                                    bot_token=token
                                )
                            except Exception as e:
                                print(e)

                            funnel_db.add_or_update_user(
                                token=token, tg_id=user, step_number=step_number + 1, trigger_time=user_trigger_time
                            )




event_loop = asyncio.get_event_loop()
while True:
    #event_loop.run_until_complete(asyncio.sleep(60))
    event_loop.run_until_complete(funnel_mailing())