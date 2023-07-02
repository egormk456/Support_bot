from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, CallbackQuery, ContentTypes
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.dispatcher import FSMContext

from markups.back_markups import (
    back_to_menu_markup,
    back_to_funnel_settings,
    back_to_funnel_steps,
)

from markups.markups_file import (
    funnel_markup,
    bots_markup,
    funnel_steps_markup,
)

from handlers.bot_states import AddBotStates, FunnelStates
from config import token
from utils.db_api.database import Database
from utils.db_api.funnel_db import FunnelDatabase

bot = Bot(token=token)
memory = MemoryStorage()
dp = Dispatcher(bot=bot, storage=memory)
db = Database(name="comments.db")
funnel_db = FunnelDatabase(name="funnels.db")


@dp.message_handler(commands=["start"], state="*")
async def start_handler(message: Message, state: FSMContext):
    await message.answer(text="Bot – это конструктор ботов обратной связи в Telegram.", reply_markup=bots_markup)


@dp.callback_query_handler(state="*")
async def callback_handler(call: CallbackQuery, state: FSMContext):
    #print(call)
    chat = call.message.chat.id
    tg_id = call["from"]["id"]
    callback = call.data
    mess_id = call.message.message_id
    tokens = db.get_tokens(tg_id=tg_id)
    funnel_tokens = funnel_db.get_tokens(tg_id=tg_id)

    user_state = await state.get_state()
    #print(user_state, type(user_state))
    #print(callback)
    if callback == "add-bot":
        await AddBotStates.add_bot.set()

        settings_message = await bot.send_message(
            chat_id=chat,
            text="Чтобы подключить бот, вам нужно выполнить два действия:\n\n"
                 "1. Перейдите в @BotFather и создайте новый бот.\n"
                 "2. После создания бота вы получите токен (12345:6789ABCDEF) — скопируйте или перешлите его в этот чат.\n\n"
                 "Важно: не подключайте боты, которые уже используются другими сервисами (Controller Bot, разные CRM и т.д.)",
            reply_markup=back_to_menu_markup
        )

        async with state.proxy() as data:
            data["message_id"] = settings_message.message_id

    elif callback == "my-bots":
        bots_username_markup = InlineKeyboardMarkup()

        if tokens is not None and len(tokens) > 0:
            for token in tokens:
                botik = Bot(token)
                user_bot = await botik.me
                bot_username = user_bot.username
                bots_username_markup.add(InlineKeyboardButton(text=f"@{bot_username}", url=f"https://t.me//{bot_username}"))
            text = "Выберите бота из списка ниже"

        else:
            text = "У вас пока нет ни одного бота"

        bots_username_markup.add(InlineKeyboardButton(text="Назад", callback_data="back-to-menu"))

        await bot.delete_message(
            chat_id=tg_id,
            message_id=mess_id
        )

        await bot.send_message(
            chat_id=chat,
            text=text,
            reply_markup=bots_username_markup
        )

    elif callback == "help":
        await bot.delete_message(
            chat_id=tg_id,
            message_id=mess_id
        )

        await bot.send_message(
            chat_id=chat,
            text="По всем вопросам пишите: @egormk",
            reply_markup=back_to_menu_markup
        )

    elif callback == "back-to-menu":
        await bot.delete_message(
            chat_id=tg_id,
            message_id=mess_id
        )

        async with state.proxy() as data:
            try:
                await bot.delete_message(
                    chat_id=tg_id,
                    message_id=data["message_id"]
                )
            except Exception:
                #print("message_id", data)
                pass

            try:
                await bot.delete_message(
                    chat_id=tg_id,
                    message_id=data["token_is_used"]
                )
            except Exception:
                pass

            try:
                await bot.delete_message(
                    chat_id=tg_id,
                    message_id=data["incorrect_token"]
                )
            except Exception:
                pass

            try:
                await bot.delete_message(
                    chat_id=tg_id,
                    message_id=data["used_token_message"]
                )
            except Exception:
                pass

        await state.finish()
        await call.message.answer(
            text="Bot – это конструктор ботов обратной связи в Telegram.",
            reply_markup=bots_markup
        )

    elif callback in ["funnel-settings", "back-to-fs"]:
        await state.finish()
        await bot.delete_message(
            chat_id=tg_id,
            message_id=mess_id
        )

        await bot.send_message(
            chat_id=chat,
            text="Настройка автоворонок",
            reply_markup=funnel_markup,
        )

    elif callback == "add-funnel":
        await FunnelStates.add_funnel.set()
        funnel_username_markup = InlineKeyboardMarkup()

        await bot.delete_message(
            chat_id=tg_id,
            message_id=mess_id
        )

        if tokens is not None and len(tokens) > 0:
            text = "Сначала нужно добавить бота в меню. Если вы уже добавили бота в список автоворонок, перейдите в Спискок автоворонок"
            for token in tokens:
                if token not in funnel_tokens:
                    #print(token, funnel_tokens)
                    text = "Выберите бота из списка ниже"
                    botik = Bot(token)
                    user_bot = await botik.me
                    bot_username = user_bot.username
                    funnel_username_markup.add(
                        InlineKeyboardButton(
                            text=f"@{bot_username}",
                            callback_data=f"{token}"
                        )
                    )

                funnel_username_markup.add(
                    InlineKeyboardButton(text="Назад", callback_data="back-to-fs")
                )



            await bot.send_message(
                chat_id=tg_id,
                text=text,
                reply_markup=funnel_username_markup,
            )

        else:
            text = "Сначала добавьте бота в Меню"

            await bot.send_message(
                chat_id=tg_id,
                text=text,
                reply_markup=back_to_funnel_settings
            )

    elif callback == "funnel-list":
        funnel_username_markup = InlineKeyboardMarkup()

        await bot.delete_message(
            chat_id=tg_id,
            message_id=mess_id
        )

        if funnel_tokens is not None and len(funnel_tokens) > 0:
            for token in funnel_tokens:
                botik = Bot(token)
                user_bot = await botik.me
                bot_username = user_bot.username
                funnel_username_markup.add(
                    InlineKeyboardButton(
                        text=f"@{bot_username}",
                        callback_data=f"{token}"
                    )
                )

            funnel_username_markup.add(
                InlineKeyboardButton(text="Назад", callback_data="back-to-fs")
            )

            text = "Выберите бота для дальнейшей настройки"

            await bot.send_message(
                chat_id=tg_id,
                text=text,
                reply_markup=funnel_username_markup
            )

        else:
            await bot.send_message(
                chat_id=tg_id,
                text="Добавьте бота в главном меню -> Добавить бота",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(
                        text="Вернуться в меню",
                        callback_data="back-to-menu"
                    )
                ),
            )

    elif callback in tokens and user_state == "FunnelStates:add_funnel":
        funnel_db.add_funnel(tg_id=tg_id, token=callback)
        text = "Автоворонка успешно выбрана, проведите настройку"

        async with state.proxy() as data:
            data["token"] = callback

        await bot.delete_message(
            chat_id=tg_id,
            message_id=mess_id
        )

        await bot.send_message(
            chat_id=chat,
            text=text,
            reply_markup=funnel_steps_markup,
        )

    elif callback in funnel_tokens or callback == "back-to-funnel-steps":
        await FunnelStates.funnel_steps.set()
        await bot.delete_message(
            chat_id=tg_id,
            message_id=mess_id
        )
        #print('funnel_token')
        if callback != "back-to-funnel-steps":
            async with state.proxy() as data:
                data["token"] = callback

        await bot.send_message(
            chat_id=tg_id,
            text="Настройка вашей воронки",
            reply_markup=funnel_steps_markup,
        )

    elif callback == "add-trigger":
        await FunnelStates.add_trigger.set()
        await bot.delete_message(
            chat_id=tg_id,
            message_id=mess_id
        )

        async with state.proxy() as data:
            token = data["token"]
            trigger = funnel_db.get_trigger(token=token)

            if trigger is not None:
                text = f"Нынешний триггер: {trigger}\nВведите новый триггер:",
                text = text[0]
            else:
                text = "Введите триггер:"
            #print(text, type(text))
            await bot.send_message(
                chat_id=tg_id,
                text=text,
                reply_markup=back_to_funnel_steps,
            )

    elif callback == "add-step":
        await FunnelStates.add_step.set()
        await bot.delete_message(
            chat_id=tg_id,
            message_id=mess_id
        )
        text = "Введите текст для нового шага"

        await bot.send_message(
            chat_id=tg_id,
            text=text,
            reply_markup=back_to_funnel_steps,
        )

    elif callback == "delete-step":
        await bot.delete_message(
            chat_id=tg_id,
            message_id=mess_id
        )
        async with state.proxy() as data:
            token = data["token"]

        steps = funnel_db.get_steps(token=token)
        if steps is not None:
            text = "Выберите шаг, которых хотите удалить, если вы не знаете содержание шага, то посмотрите его в списке шагов:"

            steps_markup = InlineKeyboardMarkup()
            for num, step in enumerate(steps):
                steps_markup.add(InlineKeyboardButton(text=f"Шаг №{num + 1}", callback_data=f"stepdel{num + 1}"))

            steps_markup.add(InlineKeyboardButton(text="Назад", callback_data="back-to-funnel-steps"))

            await bot.send_message(
                chat_id=tg_id,
                text=text,
                reply_markup=steps_markup,
            )

        else:
            await bot.send_message(
                chat_id=tg_id,
                text="Вы пока не добавили ни одного шага",
                reply_markup=back_to_funnel_steps,
            )

    elif callback == "steps-list" or callback == "back-to-steps-list":
        await FunnelStates.steps_list.set()
        await bot.delete_message(
            chat_id=tg_id,
            message_id=mess_id
        )

        async with state.proxy() as data:
            token = data["token"]

        steps = funnel_db.get_steps(token=token)
        if steps is not None:
            text = "Ваши шаги:"

            steps_markup = InlineKeyboardMarkup()
            for num, step in enumerate(steps):
                steps_markup.add(InlineKeyboardButton(text=f"Шаг №{num + 1}", callback_data=f"step{num + 1}"))

            steps_markup.add(InlineKeyboardButton(text="Назад", callback_data="back-to-funnel-steps"))

            await bot.send_message(
                chat_id=tg_id,
                text=text,
                reply_markup=steps_markup,
            )
        else:
            await bot.send_message(
                chat_id=tg_id,
                text="Вы пока не добавили ни одного шага",
                reply_markup=back_to_funnel_steps,
            )

    elif callback[:7] == "stepdel":
        async with state.proxy() as data:
            token = data["token"]

        await bot.delete_message(
            chat_id=tg_id,
            message_id=mess_id
        )

        funnel_db.delete_step(token=token, step_number=int(callback[7:]))

        await call.answer(text=f"Шаг №{callback[7:]} успешно удалён", show_alert=True)
        text = "Автоворонка успешно выбрана, проведите настройку"

        await bot.send_message(
            chat_id=chat,
            text=text,
            reply_markup=funnel_steps_markup,
        )

    elif callback[:4] == "step":
        async with state.proxy() as data:
            token = data["token"]

        await bot.delete_message(
            chat_id=tg_id,
            message_id=mess_id
        )

        step = funnel_db.get_step_text_by_number(token=token, step_number=int(callback[4:]))

        await bot.send_message(
            chat_id=tg_id,
            text=step,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(
                    text="Назад", callback_data="back-to-steps-list"
                )
            )
        )




@dp.message_handler(content_types=ContentTypes.TEXT, state=FunnelStates.add_trigger)
async def add_trigger_handler(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    text = message.text

    async with state.proxy() as data:
        token = data["token"]
        funnel_db.add_trigger(tg_id=tg_id, token=token, trigger=text)

    await FunnelStates.funnel_steps.set()
    await bot.send_message(
        chat_id=tg_id,
        text="Триггер успешно добавлен",
        reply_markup=funnel_steps_markup,
    )


@dp.message_handler(content_types=ContentTypes.TEXT, state=FunnelStates.add_step)
async def add_step_handler(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    text = message.text

    async with state.proxy() as data:
        data["step"] = text

    await FunnelStates.add_time.set()
    await bot.send_message(
        chat_id=tg_id,
        text="Теперь введите время, через которое должно отправляться сообщение после срабатывания триггера",
    )


@dp.message_handler(content_types=ContentTypes.TEXT, state=FunnelStates.add_time)
async def add_time_handler(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    text = message.text

    if text.isdigit():
        async with state.proxy() as data:
            token = data["token"]
            step = data["step"]
            hours = int(text)
            funnel_db.add_step(tg_id=tg_id, token=token, step=step, hours=hours)

            await bot.send_message(
                chat_id=tg_id,
                text=f"Теперь через это количество часов: {hours} после срабатывания триггера будет отправляться это сообщение:"
                     f"\n\n {step}"
            )

        await FunnelStates.funnel_steps.set()
        await bot.send_message(
            chat_id=tg_id,
            text="Шаг успешно добавлен",
            reply_markup=funnel_steps_markup,
        )

    else:
        await bot.send_message(
            chat_id=tg_id,
            text="Количество часов должно быть целым числом",
        )


@dp.message_handler(content_types=ContentTypes.TEXT)
async def text_handler(message: Message, state: FSMContext):
    text = message.text

    if text == "token":
        await AddBotStates.add_bot.set()


@dp.message_handler(state=AddBotStates.add_bot)
async def add_bot_state(message: Message, state: FSMContext):
    text = message.text
    tg_id = message.from_user.id
    mess_id = message.message_id
    menu = InlineKeyboardMarkup().add(InlineKeyboardButton(text="Вернуться в меню", callback_data="back-to-menu"))

    if text[:10].isdigit() and text[10] == ":":
        try:
            tokens = db.get_tokens()

            if tokens is None or text not in tokens:
                db.add_bot(
                    tg_id=tg_id,
                    bot_token=text
                )

                db.start_message(
                    method="save",
                    bot_token=text,
                    text="Стартовое сообщение"
                )

                async with state.proxy() as data:
                    try:
                        await bot.delete_message(
                            chat_id=tg_id,
                            message_id=data["message_id"]
                        )
                    except Exception:
                        pass

                    try:
                        await bot.delete_message(
                            chat_id=tg_id,
                            message_id=data["token_is_used"]
                        )
                    except Exception:
                        pass

                    try:
                        await bot.delete_message(
                            chat_id=tg_id,
                            message_id=data["incorrect_token"]
                        )
                    except Exception:
                        pass

                    try:
                        await bot.delete_message(
                            chat_id=tg_id,
                            message_id=data["used_token_message"]
                        )
                    except Exception:
                        pass

                await bot.delete_message(
                    chat_id=tg_id,
                    message_id=mess_id
                )

                await bot.send_message(
                    chat_id=tg_id,
                    text="Бот успешно добавлен\n\n"
                         "Теперь, чтобы бот работал, создайте канал и группу с комментариями, откройте комментарии в канале,"
                         " добавьте бота в канал и группу, сделайте его админом. После данных настроек напиши пост в канале -"
                         " /set_group. На этом настройка бота будет завершена.",
                    reply_markup=menu
                )
                await state.finish()

            else:
                token_is_used = await bot.send_message(
                    chat_id=tg_id,
                    text="Данный токен уже используется",
                    reply_markup=menu
                )

                async with state.proxy() as data:
                    data["used_token_message"] = message.message_id
                    data["token_is_used"] = token_is_used.message_id
                    #print(data)

        except Exception as e:
            #print(e)
            pass


    else:
        incorrect_token = await bot.send_message(
            chat_id=tg_id,
            text="Некорректный токен",
            reply_markup=menu
        )

        async with state.proxy() as data:
            data["incorrect_token"] = incorrect_token.message_id
            #print(data)


executor.start_polling(dispatcher=dp, skip_updates=True)