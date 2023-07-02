from aiogram import Bot
from datetime import datetime
from utils.db_api.database import Database
from utils.db_api.funnel_db import FunnelDatabase

import asyncio
used_tokens = []


async def funnel_mailing():
    db = Database("comments.db")
    funnel_db = FunnelDatabase("funnels.db")

    now_hour = datetime.now().hour
    now_day = datetime.now().day
    tokens = funnel_db.get_tokens()
    for token in tokens:
        bot = Bot(token=token)
        chat_id = db.get_chat_link(bot_token=token)
        group_id = db.get_group_id(bot_token=token)
        funnel_users = funnel_db.get_users(token=token)
        funnel_users = [user[0] for user in funnel_users]

        for user in funnel_users:
            user_step_number, user_trigger_time = funnel_db.get_user_step_number_and_time(tg_id=user, token=token)
            steps_hours_steps_number = funnel_db.get_steps_info(token=token)
            user_trigger_hour, user_trigger_day = user_trigger_time.split(" ")

            if steps_hours_steps_number is not None:
                for step, hour, step_number in steps_hours_steps_number:
                    user_trigger_hour = int(user_trigger_hour)
                    user_trigger_day = int(user_trigger_day)

                    tt = user_trigger_hour + hour
                    if tt > 24:
                        tt = tt - 24
                        user_trigger_day += 1

                    #print(type(now_day), type(user_trigger_day))
                    if (tt == now_hour and user_trigger_day == now_day and step_number == user_step_number)\
                            or (now_day > user_trigger_day or tt < now_hour and step_number == user_step_number):
                        funnel_message = await bot.send_message(
                            chat_id=user,
                            text=step,
                            parse_mode="html"
                        )

                        try:
                            await bot.copy_message(
                                chat_id=group_id,
                                from_chat_id=user,
                                message_id=funnel_message.message_id,
                                reply_to_message_id=db.get_post_id(tg_id=user, bot_token=token)
                            )
                        except Exception:
                            pass

                        db.add_user_message(
                            tg_id=user,
                            message_id=funnel_message.message_id,
                            bot_token=token
                        )

                        funnel_db.add_or_update_user(
                            token=token, tg_id=user, step_number=step_number + 1, trigger_time=user_trigger_time
                        )



if __name__ == '__main__':
    event_loop = asyncio.get_event_loop()
    while True:
        #event_loop.run_until_complete(asyncio.sleep(60))
        event_loop.run_until_complete(funnel_mailing())