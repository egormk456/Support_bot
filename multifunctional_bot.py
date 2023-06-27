from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, CallbackQuery, ContentTypes
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.dispatcher import FSMContext

from markups.bots_markup import bots_markup
from markups.back_to_menu_markup import back_to_menu_markup
from handlers.addbot_states import AddBotStates
from config import token
from utils.db_api.database import Database

bot = Bot(token=token)
memory = MemoryStorage()
dp = Dispatcher(bot=bot, storage=memory)
db = Database(name="comments.db")


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

    if callback == "add-bot":
        await AddBotStates.add_bot.set()

        await bot.delete_message(
            chat_id=chat,
            message_id=mess_id
        )

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
        tokens = db.get_tokens(tg_id=tg_id)

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
            chat_id=chat,
            message_id=mess_id
        )

        await bot.send_message(
            chat_id=chat,
            text=text,
            reply_markup=bots_username_markup
        )

    elif callback == "help":
        await bot.delete_message(
            chat_id=chat,
            message_id=mess_id
        )

        await bot.send_message(
            chat_id=chat,
            text="По всем вопросам пишите: @egormk",
            reply_markup=back_to_menu_markup
        )

    elif callback == "back-to-menu":
        await bot.delete_message(
            chat_id=chat,
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
            print(e)


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