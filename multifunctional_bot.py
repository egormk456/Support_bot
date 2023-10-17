from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, CallbackQuery, ContentTypes
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.dispatcher import FSMContext

from markups.back_markups import (
    back_to_menu_markup,
    back_to_funnel_settings,
    back_to_funnel_steps,
    back_to_admin_markup
)

from markups.markups_file import (
    funnel_markup,
    bots_markup,
    funnel_steps_markup,
    autoanswers_markup,
    invites
)

from markups.admin_markup import admin_actions_markup

from handlers.bot_states import AddBotStates, FunnelStates, BotStates
from config import livegram_token
from utils.db_api.database import Database
from utils.db_api.funnel_db import FunnelDatabase
from utils.db_api.admin_database import AdminDatabase
from utils.usefull_functions.files_names import files_names
from utils.usefull_functions.sending_message import sending_function
from utils.usefull_functions.create_markup import create_markup
from xlsxwriter import Workbook
import os


admin_dict = {
    "Посмотреть статистику": "get-statistics",
    "Изменить стартовое сообщение": "edit-start-message",
    "Настройка автоворонки": "funnel-settings",
    "Автоответы": "autoanswers",
    "Пригласительные ссылки": "invites_links",
    "Передать бота": "transfer_bot",
    "Удалить бота": "delete_bot",
    "К списку ботов": "back-to-my-bots"
}



start_text = "<b>CustomerLive</b> – это конструктор ботов обратной связи в Telegram. Подробности читайте в " \
             "<a href='https://telegra.ph/CustomerLive--spravka-07-18'>справке</a>.\n" \
                   "- получайте все сообщения от клиентов в одном окне\n" \
                   "- изучайте переписки с каждым пользователем по отдельности\n" \
                   "- создавайте автоворонки\n" \
                   "- создавайте команды и автоответы\n" \
                   "- все переписки с пользователями упорядочены, вы всегда можете посмотреть диалог с конкретным клиентом"

loading_text = "🕒Загружаю..."


class LivegramBot:
    def __init__(self):
        self.bot = Bot(livegram_token)
        memory = MemoryStorage()
        self.dp = Dispatcher(self.bot, storage=memory)
        self.db = Database(name="comments.db")
        self.funnel_db = FunnelDatabase(name="funnels.db")
        self.admin_db = AdminDatabase(db_name="comments.db", funnel_db_name="funnels.db")

    async def start_handler(self, message: Message, state: FSMContext):
        if message.chat.type == "private":
            await state.finish()
            text = message.text
            tg_id = message.from_user.id
            self.admin_db.add_user(tg_id=message.from_user.id)
            links_numbers = self.db.get_links_info(token=livegram_token)
            links_numbers = [elem[1] for elem in links_numbers]
            tokens = self.db.get_tokens()

            if text[7:] in tokens:
                self.db.transfer_bot(tg_id, text[7:])
                await self.bot.send_message(
                    chat_id=message.chat.id,
                    text="Теперь этот бот ваш"
                )

            else:
                if len(text[7:]) > 0 and int(text[7:]) in links_numbers:
                    self.db.update_link_views(
                        token=livegram_token,
                        link_num=int(text[7:])
                    )

                await message.answer(
                    text=start_text,
                    reply_markup=bots_markup,
                    parse_mode="html",
                    disable_web_page_preview=True
                )

    async def callback_handler(self, call: CallbackQuery, state: FSMContext):
        chat = call.message.chat.id
        tg_id = call["from"]["id"]
        callback = call.data
        mess_id = call.message.message_id
        tokens = self.db.get_tokens(tg_id=tg_id)

        user_state = await state.get_state()

        print(f"{callback =}, {user_state}")
        if callback == "back-to-menu":
            await state.finish()

            await self.bot.delete_message(
                chat_id=tg_id,
                message_id=mess_id
            )

            await self.bot.send_message(
                chat_id=chat,
                text=start_text,
                reply_markup=bots_markup,
                parse_mode="html"
            )

        # Добавление бота
        elif callback == "add-bot":
            await AddBotStates.add_bot.set()

            await self.bot.delete_message(
                chat_id=tg_id,
                message_id=mess_id
            )

            settings_message = await self.bot.send_message(
                chat_id=chat,
                text="Чтобы подключить бот, вам нужно выполнить два действия:\n"
                     "1. Перейдите в @BotFather и создайте новый бот отправив команду /newbot\n"
                     "2. После создания бота вы получите токен (12345:6789ABCDEF) — нажмите на него, он скопируется и перешлите его в этот чат\n\n"
                     "Важно: не подключайте боты, которые уже используются другими сервисами (Controller Bot, разные CRM и т.д.)",
                reply_markup=back_to_menu_markup
            )

            async with state.proxy() as data:
                data["message_id"] = settings_message.message_id

        # Второй шаг
        elif callback == "to-2-step" and user_state == "AddBotStates:step_1":
            await AddBotStates.step_2.set()

            async with state.proxy() as data:
                token = data["token"]

            bot_info = await Bot(token=token).me

            text = f"Выбранный бот: @{bot_info.username}\n\n" \
                   f"4. Откройте в канале обсуждения/комментарии.\n" \
                   f"Для этого: откройте созданный канал, нажмите на название или логотип -> нажмите «редактировать» в правом верхнем углу -> нажмите Обсуждение -> Создайте новую группу или укажите уже созданную.\n" \
                   f"5. Откройте созданную группу и добавьте в него вашего бота\n" \
                   f"6. Назначьте бота администратором группы\n\n" \
                   f"В эту группу вы можете добавить менеджеров, которые будут отвечать на сообщения клиентов.\n" \
                   f"После выполнения этих действия нажмите на кнопку ниже"


            step_2_message = await self.bot.send_message(
                chat_id=tg_id,
                text=text,
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="Далее >>>", callback_data="to-3-step")
                )
            )

            async with state.proxy() as data:
                data["step_2"] = step_2_message.message_id

        # Третий шаг
        elif callback == "to-3-step" and user_state == "AddBotStates:step_2":
            async with state.proxy() as data:
                token = data["token"]

            bot_info = await Bot(token=token).me

            text = f"Выбранный бот: @{bot_info.username}\n\n" \
                   f"Остался последний шаг!\n" \
                   f"После того, как вы добавили бота в канал и группу и сделали его администратором, напишите в канале пост: /set_group\n\n" \
                   f"Если вы все сделали верно, бот пришлет сообщение в группу “Настройка прошла успешно”\n" \
                   f"Теперь можете удалять сообщение настройки.\n\n" \
                   f"Если бот ничего не написал, проверьте, везде ли бот является администратором и повторите /set_group\n" \
                   f"В случае возникновения проблем, пишите сюда – @egormk"

            step_3_message = await self.bot.send_message(
                chat_id=tg_id,
                text=text,
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="Готово", callback_data="bot_added")
                )
            )

            async with state.proxy() as data:
                data["step_3"] = step_3_message.message_id

        # Бот добавлен!
        elif callback == "bot_added":
            if callback == "bot_added":
                async with state.proxy() as data:
                    token = data["token"]

                    step_1 = data.get("step_1")
                    step_2 = data.get("step_2")
                    step_3 = data.get("step_3")
                    message_id = data.get("message_id")
                    token_is_used = data.get("token_is_used")
                    incorrect_token = data.get("incorrect_token")
                    used_token_message = data.get("used_token_message")

                    steps = [
                        step_1, step_2,
                        step_3, message_id,
                        token_is_used,
                        incorrect_token,
                        used_token_message
                    ]

                    for step in steps:
                        if step is not None:
                            try:
                                await self.bot.delete_message(
                                    chat_id=tg_id,
                                    message_id=step
                                )
                            except Exception:
                                pass

                bot_info = await Bot(token).me

                text = f"Бот @{bot_info.username} успешно подключен к CustomerLive.\n" \
                       f"Попробуйте отправить боту любое сообщение, а затем ответить на него. " \
                       f"Сообщение придет в группу, а в канале создастся пост, в котором будет храниться переписка с клиентом.\n\n" \
                       f"<b>Как отвечать на входящие сообщения?</b>\n" \
                       f"Сообщения от клиентов будут приходить в группу, которую вы создали,используйте встроенную функцию Telegram для <a href='https://telegram.org/tour/groups#replies'>ответов</a>. Для этого сделайте свайп влево (или кликните два раза) по сообщению, на которое хотите ответить.\n\n" \
                       f"<b>Как изменить приветственное сообщение?</b>\n" \
                       f"Чтобы изменить приветствие, нажмите кнопку «Мои боты» и перейдите в раздел «Изменить стартовое сообщение».\n\n" \
                       f"<b>Как добавить автоответы?</b>\n" \
                       f"Чтобы добавить автоответы, нажмите кнопку «Мои боты» и перейдите в раздел «Добавить команду».\n\n" \
                       f"<b>Как добавить автоворонку?</b>\n" \
                       f"Чтобы добавить автоворонку  нажмите кнопку «Мои боты» и перейдите в раздел “Настройка автоворонки”\n\n" \
                       f"Полную информацию о работе бота можно посмотреть <a href='https://telegra.ph/CustomerLive--spravka-07-18'>справке</a> о работе CustomerLive"


                await self.bot.send_message(
                    chat_id=chat,
                    text=text,
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton(
                            text=f"Настроить бота: {bot_info.username}", callback_data=token),
                    ),
                    parse_mode="html",
                    disable_web_page_preview=True
                )
                await state.finish()
                await BotStates.bot_list.set()



        # Список ботов
        elif callback == "my-bots" or callback == "back-to-my-bots":
            await BotStates.bot_list.set()
            bots_username_markup = InlineKeyboardMarkup()

            if tokens is not None and len(tokens) > 0:
                for token in tokens:
                    botik = Bot(token)
                    user_bot = await botik.me
                    bot_username = user_bot.username
                    bots_username_markup.add(InlineKeyboardButton(text=f"@{bot_username}", callback_data=token))
                text = "Выберите бота, чтобы настроить его"

            else:
                text = "У вас пока нет ни одного бота"

            bots_username_markup.add(InlineKeyboardButton(text="Назад", callback_data="back-to-menu"))

            await self.bot.delete_message(
                chat_id=tg_id,
                message_id=mess_id
            )

            await self.bot.send_message(
                chat_id=chat,
                text=text,
                reply_markup=bots_username_markup
            )



        elif callback in ["add_application", "don't_add_application"]:
            await self.bot.delete_message(
                chat_id=tg_id,
                message_id=mess_id
            )

            if callback == "don't_add_application":
                await self.add_info(chat=chat, state=state)

            else:
                await BotStates.add_application_text.set()
                await self.bot.send_message(
                    chat_id=chat,
                    text="Введите текст, который пользователь будет видеть при нажатии на кнопку заявки, ограничение - 1000 символов",
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton(text="Вернуться к настройкам бота", callback_data="back-to-admin")
                    )
                )

        # Настройки бота
        elif tokens is not None and callback in tokens and user_state == "BotStates:bot_list" \
                or callback == "back-to-admin":
            await BotStates.bot_settings.set()

            await self.bot.delete_message(
                chat_id=tg_id,
                message_id=mess_id
            )

            if callback == "back-to-admin":
                async with state.proxy() as data:
                    token = data["token"]

                await state.finish()
                await BotStates.bot_settings.set()
                async with state.proxy() as data:
                    data["token"] = token
                bot_info = await Bot(token).me

            else:
                bot_info = await Bot(callback).me

            admin_markup = InlineKeyboardMarkup()
            admin_markup.add(
                InlineKeyboardButton(
                    text="Рассылка пользователям",
                    url=f"https://t.me/{bot_info.username}?start=1111111"
                )
            )


            for key, value in admin_dict.items():
                admin_markup.add(
                    InlineKeyboardButton(text=key, callback_data=value)
            )


            if callback != "back-to-admin":
                async with state.proxy() as data:
                    data["token"] = callback


                    data["username"] = bot_info.username

                await self.bot.send_message(
                    chat_id=tg_id,
                    text=f"Настройка для бота: @{bot_info.username}",
                    reply_markup=admin_markup
                )

            else:
                async with state.proxy() as data:
                    data["username"] = bot_info.username
                    sending_id = data.get("sending_message_id")
                    user_message_id = data.get("user_message_id")
                    instruction_message_id = data.get("instruction_message_id")

                    messages_list = [sending_id, user_message_id, instruction_message_id]

                    for id in messages_list:

                        if id is not None:
                            try:
                                await self.bot.delete_message(
                                    chat_id=chat,
                                    message_id=id
                                )
                            except Exception as e:
                                print(e, 250)

                await self.bot.send_message(
                    chat_id=tg_id,
                    text=f"Настройка для бота: @{bot_info.username}",
                    reply_markup=admin_markup
                )

        # Статистика
        elif callback == "get-statistics":
            async with state.proxy() as data:
                token = data["token"]

            response = self.db.get_statistics(bot_token=token)
            text = f"<b>Статистика обновляется после рассылки</b>\n\n" \
                   f"Всего пользователей: {response['all_users']}\n" \
                   f"Пользователей, заблокировавших бота: {response['blocked']}\n" \
                   f"Пользователей, не заблокировавших бота: {response['unblocked']}"

            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=mess_id
            )

            await self.dp.bot.send_message(
                chat_id=chat,
                text=text,
                reply_markup=back_to_admin_markup,
                parse_mode="html"
            )

        #передача бота
        elif callback == "transfer_bot":
            async with state.proxy() as data:
                token = data["token"]

            await self.bot.send_message(
                chat_id=chat,
                text=f"Если вы хотите передать бота человеку, пусть введёт в боте:\n"
                     f"/start {token}",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="Вернуться к найстройкам бота", callback_data="back-to-admin"),
                )
            )

        # Удаление бота
        elif callback == "delete_bot":
            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=mess_id
            )

            await BotStates.delete_bot.set()

            async with state.proxy() as data:
                token = data["token"]

            bot_info = await Bot(token).me

            await self.bot.send_message(
                chat_id=chat,
                text=f"Вы хотите удалить бота @{bot_info.username}?",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="Да", callback_data="Yes"),
                    InlineKeyboardButton(text="Нет", callback_data="back-to-admin")
                )
            )

        elif callback == "Yes" and user_state == "BotStates:delete_bot":
            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=mess_id
            )

            async with state.proxy() as data:
                token = data["token"]
                self.db.delete_bot(token=token)
                self.funnel_db.delete_bot(token=token)

            await self.bot.send_message(
                chat_id=chat,
                text="Бот успешно удалён",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="К списку ботов", callback_data="back-to-my-bots")
                )
            )

            await state.finish()




        # Автоответы
        elif callback == "autoanswers":
            await BotStates.bot_settings.set()
            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=mess_id
            )

            async with state.proxy() as data:
                token = data["token"]

            commands_list = self.db.get_commands_list(bot_token=token)

            if commands_list is not None:
                commands = [f"\n{num + 1}) {command}" for num, command in enumerate(commands_list)]
                text = "У вас установлены автоответы на команды:" + "".join(commands)
            else:
                text = "Вы не добавили ни одной команды"


            await self.dp.bot.send_message(
                chat_id=chat,
                text=text,
                reply_markup=autoanswers_markup,
                parse_mode="html"
            )

        # Добавление команды с автоответом
        elif callback == "add-command":
            await BotStates.add_command.set()

            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=mess_id
            )

            await self.dp.bot.send_message(
                chat_id=chat,
                text="Добавьте фразу, на которую пользователь должен получать автоответ\n"
                     "Это может быть просто слово, например привет или любая команда <i>/gift</i>",
                reply_markup=back_to_admin_markup,
                parse_mode="html"
            )

        # Изменение автоответа
        elif callback in ["edit-text-command", "edit-command"]:
            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=mess_id
            )

            if callback == "edit-text-command":
                await BotStates.choose_command.set()
                message_text = "Введите название команды, описание которой хотите изменить"
                command_mode = "autoanswer"

            else:
                await BotStates.edit_command.set()
                message_text = "Выберите команду, которую хотите изменить\n\n" \
                               "ВАЖНО: автоответ этой команды перейдёт на новую команду"
                command_mode = "command"

            async with state.proxy() as data:
                token = data["token"]
                data["command_mode"] = command_mode

            commands_list = self.db.get_commands_list(bot_token=token)


            if commands_list is not None:
                commands = "".join([f"{num + 1}) {command}\n" for num, command in enumerate(commands_list)])
                message_text = message_text + "\nДоступный список команд:\n" + commands

            elif commands_list is None:
                message_text = "Пока нет ни одной команды."


            await self.dp.bot.send_message(
                chat_id=chat,
                text=message_text,
                reply_markup=back_to_admin_markup
            )

        # Удаление команды
        elif callback == "delete-command":
            await BotStates.delete_command.set()
            async with state.proxy() as data:
                token = data["token"]

            commands_list = self.db.get_commands_list(bot_token=token)
            message_text = "Введите название команды, которую хотите удалить."

            if commands_list is not None:
                commands = "".join([f"{num + 1}) {command}\n" for num, command in enumerate(commands_list)])
                message_text = message_text + "\nДоступный список команд:\n" + commands

            elif commands_list is None:
                message_text = "Пока нет ни одной команды."

            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=mess_id
            )

            await self.dp.bot.send_message(
                chat_id=chat,
                text=message_text,
                reply_markup=back_to_admin_markup
            )

        # Пригласительные ссылки

        elif callback == "invites_links":
            await BotStates.invites_links.set()
            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=mess_id
            )

            await self.bot.send_message(
                chat_id=chat,
                text="Здесь вы можете создать пригласительные ссылки, чтобы отслеживать, откуда пришли подписчики",
                reply_markup=invites
            )

        # Список пригласительных ссылок
        elif callback == "get_invites_links" or callback == "AGIL":
            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=mess_id
            )

            async with state.proxy() as data:
                token = data.get("token")
                markup = InlineKeyboardMarkup().add(
                    InlineKeyboardButton(
                        text="Назад к пригласительным ссылкам",
                        callback_data="invites_links"
                    )
                )

            if callback == "AGIL":
                token = livegram_token
                markup = None

            links_info = self.db.get_links_info(token=token)

            if links_info is None or len(links_info) == 0:
                await self.bot.send_message(
                    chat_id=chat,
                    text="Вы не создали ни одной ссылки",
                    reply_markup=markup
                )

            else:
                bot_info = await Bot(token).me
                for name, invite_link_number, people_from_link in links_info:
                    text = f"Ссылка: https://t.me/{bot_info.username}?start={invite_link_number}\n" \
                           f"Название ссылки: {name}\n" \
                           f"Присоединилось по ссылке: {people_from_link}"

                    await self.bot.send_message(
                        chat_id=chat,
                        text=text,
                        disable_web_page_preview=True,
                        reply_markup=InlineKeyboardMarkup().add(
                            InlineKeyboardButton(
                                text="Удалить",
                                callback_data=f"delete_link_{invite_link_number}"
                            )
                        )
                    )

                await self.bot.send_message(
                    chat_id=chat,
                    text=f"Всего ссылок: {len(links_info)}",
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton(
                            text="Назад",
                            callback_data="invites_links"
                        )
                    )
                )

        # Удаление ссылки
        elif callback[:12] == "delete_link_":
            async with state.proxy() as data:
                token = data["token"]
            await self.bot.delete_message(
                chat_id=chat,
                message_id=mess_id
            )

            self.db.delete_invite_link(
                token=token,
                link_num=int(callback[12:])
            )

            await call.answer(text="Пригласительная ссылка удалена", show_alert=True)


        # Добавление ссылки
        elif callback == "add_invite_link" or callback == "AAIL":
            await BotStates.add_invite_link.set()

            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=mess_id
            )

            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton(
                    text="Назад к пригласительным ссылкам",
                    callback_data="invites_links"
                )
            )

            if callback == "AAIL":
                async with state.proxy() as data:
                    data["token"] = livegram_token
                    markup = None

            text = "Введите название пригласительной ссылки или вернитесь назад"
            instruction_message = await self.bot.send_message(
                chat_id=chat,
                text=text,
                disable_web_page_preview=True,
                reply_markup=markup
            )

            async with state.proxy() as data:
                data["instruction_message_id"] = instruction_message.message_id

        # Стартовое сообщение
        elif callback == "edit-start-message":
            await BotStates.edit_start_message.set()

            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=mess_id
            )

            text = "Стартовое сообщение - первое сообщение, которое получит пользователь при запуске бота\n\n" \
                   "Установите стартовое сообщение, доступные форматы:\n" \
                   "1) Текст (поддерживается форматирование)\n" \
                   "2) Фото\n" \
                   "3) Фото с текстом\n" \
                   "4) Голосовое сообщение\n" \
                   "5) Видео\n" \
                   "6) Видеосообщение\n" \
                   "7) PDF-файлы"

            instruction_message = await self.dp.bot.send_message(
                chat_id=chat,
                text=text,
                reply_markup=back_to_admin_markup
            )
            async with state.proxy() as data:
                data["instruction_message_id"] = instruction_message.message_id

        # Помощь
        elif callback == "help":
            await self.bot.delete_message(
                chat_id=tg_id,
                message_id=mess_id
            )

            await self.bot.send_message(
                chat_id=chat,
                text="Полную информацию о работе бота можете прочитать в <a href='https://telegra.ph/CustomerLive--spravka-07-18'>справке</a>.\n\n"
                     "По другим вопросам пишите: @egormk",
                parse_mode="html",
                reply_markup=back_to_menu_markup,
                disable_web_page_preview=True
            )




        # Настройки воронки
        elif callback == "funnel-settings" or callback == "back-to-funnel-steps":
            await FunnelStates.funnel_steps.set()
            await self.bot.delete_message(
                chat_id=tg_id,
                message_id=mess_id
            )

            async with state.proxy() as data:
                token = data["token"]
                bot_info = await Bot(token).me

            is_trigger = self.funnel_db.get_trigger(token=token)

            if is_trigger is None:
                trigger_text = "\nДля настройки автоворонки установите триггер"

            else:
                trigger_text = f"\nУстановлен триггер: {is_trigger}"

            await self.bot.send_message(
                chat_id=tg_id,
                text=f"Настройка вашей воронки: @{bot_info.username}" + trigger_text,
                reply_markup=funnel_steps_markup,
            )

        # Добавление триггера
        elif callback == "add-trigger":
            await FunnelStates.add_trigger.set()
            await self.bot.delete_message(
                chat_id=tg_id,
                message_id=mess_id
            )

            async with state.proxy() as data:
                token = data["token"]
                trigger = self.funnel_db.get_trigger(token=token)

                if trigger is not None:
                    trigger_text = f"\n\nНынешний триггер: {trigger}\nВведите новый триггер:",

                else:
                    trigger_text = "\n\nВведите триггер:"

                text = "Установите триггер, который даст понять боту, что надо запускать автоворонку.\n" \
                       "Триггер может быть только один и триггером может быть определенное слово, например ”привет” или  любая команда, например /gift или /подарок.\n" \
                       "Если вы хотите, чтобы автоворонка начинала работать, как только пользователь запустил бота, установите триггер: /start"

                await self.bot.send_message(
                    chat_id=tg_id,
                    text=text + trigger_text[0],
                    reply_markup=back_to_funnel_steps,
                )

        # Добавление шага
        elif callback == "add-step":
            await FunnelStates.add_step.set()
            await self.bot.delete_message(
                chat_id=tg_id,
                message_id=mess_id
            )
            text = f"Отправьте сообщение для шага\n" \
                   f"Допустимые форматы: (текст, фото, фото с текстом, видеосообщение-кружок, аудиосообщение/голосовое сообщение, pdf-файл, pdf-файл с подписью)\n" \
                   f"Можете прислать сообщение сами или сделать репост уже готового сообщения\n\n" \
                   f"ВАЖНО: в шаг можно загрузить только одно фото, если вы отправите несколько фото, то будет взять первое из них"

            await self.bot.send_message(
                chat_id=tg_id,
                text=text,
                reply_markup=back_to_funnel_steps,
            )

        # Список шагов
        elif callback == "steps-list" or callback == "back-to-steps-list" or callback == "delete-step":
            await self.bot.delete_message(
                chat_id=tg_id,
                message_id=mess_id
            )

            async with state.proxy() as data:
                token = data["token"]
                time_id = data.get("time_message_id")

                if time_id is not None:
                    try:
                        await self.bot.delete_message(
                            chat_id=tg_id,
                            message_id=time_id
                        )
                    except:
                        pass

            steps = self.funnel_db.get_steps(token=token)
            if steps is not None:
                if callback == "delete-step":
                    text = "Выберите шаг, которых хотите удалить, если вы не знаете содержание шага, то посмотрите его в списке шагов:"
                    await FunnelStates.delete_step.set()
                else:
                    text = "Ваши шаги:"
                    await FunnelStates.steps_list.set()

                steps_markup = InlineKeyboardMarkup()
                for num, step in enumerate(steps):
                    steps_markup.add(InlineKeyboardButton(text=f"Шаг №{num + 1}", callback_data=f"step{num + 1}"))

                steps_markup.add(InlineKeyboardButton(text="Назад", callback_data="back-to-funnel-steps"))

                await self.bot.send_message(
                    chat_id=tg_id,
                    text=text,
                    reply_markup=steps_markup,
                )
            else:
                await self.bot.send_message(
                    chat_id=tg_id,
                    text="Вы пока не добавили ни одного шага",
                    reply_markup=back_to_funnel_steps,
                )

        # Удаление шага
        elif callback[:7] == "stepdel":
            print(user_state)
            async with state.proxy() as data:
                token = data["token"]

                time_id = data.get("time_message_id")

                if time_id is not None:
                    await self.bot.delete_message(
                        chat_id=tg_id,
                        message_id=time_id
                    )

            await self.bot.delete_message(
                chat_id=tg_id,
                message_id=mess_id
            )

            self.funnel_db.delete_step(token=token, step_number=int(callback[7:]))

            await call.answer(text=f"Шаг №{callback[7:]} успешно удалён", show_alert=True)
            bot_info = await Bot(token).me
            is_trigger = self.funnel_db.get_trigger(token=token)

            if is_trigger is None:
                trigger_text = "\nДля настройки автоворонки установите триггер"

            else:
                trigger_text = f"\nУстановлен триггер: {is_trigger}"

            await FunnelStates.funnel_steps.set()
            await self.bot.send_message(
                chat_id=tg_id,
                text=f"Настройка воронки @{bot_info.username}" + trigger_text,
                reply_markup=funnel_steps_markup,
            )

        # Просмотр шага
        elif callback[:4] == "step":
            print(user_state)
            async with state.proxy() as data:
                token = data["token"]

            await self.bot.delete_message(
                chat_id=tg_id,
                message_id=mess_id
            )

            loading_message = await self.bot.send_message(
                chat_id=tg_id,
                text=loading_text
            )

            try:
                hours, minutes = self.funnel_db.get_step_time(token=token, step_number=int(callback[4:]))
            except TypeError:
                hours, minutes = self.funnel_db.get_step_time(token=token, step_number=int(callback[4:]))
            step_info = self.funnel_db.get_step_by_number(token=token, step_number=int(callback[4:]))
            step, audio, photo, video, video_note, document, document_name, markup_text, application_text, application_button, application_name = step_info

            markup = InlineKeyboardMarkup()

            if application_button is None:
                application_button = "Оставить заявку"

            if application_name is not None:
                markup.add(
                    InlineKeyboardButton(
                        text=application_button, callback_data=application_name
                    )
                )

            commands_list = self.db.get_commands_list(bot_token=token)
            if markup_text != "0":
                markup = create_markup(markup_text=markup_text, markup=markup, commands_list=commands_list)

            if user_state == "FunnelStates:delete_step":
                markup.add(
                    InlineKeyboardButton(
                        text="Удалить данный шаг",
                        callback_data=f"stepdel{callback[4:]}"
                    )).add(
                        InlineKeyboardButton(
                            text="Назад",
                            callback_data="delete-step"
                        )
                    )


            else:
                markup.add(
                    InlineKeyboardButton(
                        text="Назад", callback_data="back-to-steps-list"
                    )
                )

            time_text = f"Шаг отправляется через {hours}/{minutes} часов/минут после активации триггера"

            time_message = await self.bot.send_message(
                chat_id=chat,
                text=time_text
            )

            async with state.proxy() as data:
                data["time_message_id"] = time_message.message_id

            sending_message = await sending_function(
                bot=self.bot,
                chat_id=chat,
                text=step,
                audio=audio,
                photo=photo,
                video=video,
                video_note=video_note,
                document=document,
                document_name=document_name,
                markup=markup
            )

            await self.bot.delete_message(
                chat_id=tg_id,
                message_id=loading_message.message_id
            )




        # Админка
        elif callback == "get-admin-statistics":
            statistics_dict = self.admin_db.get_statistics()
            if statistics_dict is None:
                await self.bot.send_message(
                    chat_id=chat,
                    text="Пока ни одного пользователя не нажало на старт"
                )

            else:
                wb: Workbook = Workbook("users-list.xlsx")
                worksheet = wb.add_worksheet()

                if os.path.isfile("users-list.xlsx"):
                    os.remove("users-list.xlsx")

                row: int = 0  # номер строки

                worksheet.write(row, 0, "id")
                worksheet.write(row, 1, "bots_count")
                worksheet.write(row, 2, "funnels_count")
                worksheet.write(row, 3, "users_count")
                worksheet.write(row, 4, "bots_urls")

                for user_id, user_info in statistics_dict.items():
                    bots_urls = [await Bot(token).me for token in user_info["tokens"]]
                    bots_urls = [f"@{bot.username}" for bot in bots_urls]

                    row += 1
                    worksheet.write(row, 0, user_id)
                    worksheet.write(row, 1, len(user_info["tokens"]))
                    worksheet.write(row, 2, user_info["funnel_count"])
                    worksheet.write(row, 3, user_info["users_count"])
                    worksheet.write(row, 4, ", ".join(bots_urls))

                wb.close()

                await self.bot.delete_message(
                    chat_id=chat,
                    message_id=mess_id
                )

                with open("users-list.xlsx", "rb") as document:
                    await self.bot.send_message(
                        chat_id=chat,
                        text="Файл с данными о всех пользователях:"
                    )

                    await self.bot.send_document(
                        chat_id=chat,
                        document=document
                    )
                    os.remove("users-list.xlsx")

                await self.bot.send_message(
                    chat_id=chat,
                    text="Выберите опцию",
                    reply_markup=admin_actions_markup
                )

        # Рассылка по дочерним ботам
        elif callback == "bots-mailing":
            await BotStates.admin_mailing_all_users.set()
            await self.bot.send_message(
                chat_id=chat,
                text="Следующее сообщение, которое вы отправите, будет переслано всем пользователям из дочерних ботов",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="Вернуться к админке", callback_data="back-to-admin")
                )
            )


        # Рассылка в главном боте
        elif callback == "mailing":
            await BotStates.admin_mailing_to_admins.set()
            await self.bot.send_message(
                chat_id=chat,
                text="Теперь вы можете отправлять любые объекты (текст, фото, стикеры - всё, что угодно.)\n\n"
                     "/cancel чтобы выйти"
            )



    async def add_invite_link_handler(self, message: Message, state: FSMContext):
        text = message.text
        markup = None

        async with state.proxy() as data:
            token = data["token"]
            instruction_message_id = data["instruction_message_id"]

        link_num = self.db.create_invite_link(
            token=token, name=text
        )

        if token != livegram_token:
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton(text="К настройкам бота", callback_data="back-to-admin")
            )

        for id in [instruction_message_id, message.message_id]:
            await self.bot.delete_message(
                chat_id=message.chat.id,
                message_id=id
            )

        bot_info = await Bot(token).me
        await self.bot.send_message(
            chat_id=message.chat.id,
            text=f"Ссылка успешно добавлена:\n"
                 f"https://t.me/{bot_info.username}?start={link_num}",
            reply_markup=markup
        )


    async def mailing_state_handler(self, message: Message, state: FSMContext):
        print(message)
        users = self.admin_db.get_users()
        chat_id = message.chat.id

        if message.text == "/cancel":
            await state.finish()
            await self.dp.bot.send_message(
                chat_id=chat_id,
                text=f"Рассылка отменена",
            )

        elif message.text == "/done":
            await self.dp.bot.send_message(
                chat_id=chat_id,
                text="🕑 Рассылка запущена!"
            )

            async with state.proxy() as data:
                mess_id = data["message_id"]

            for user in users:
                try:
                    await self.dp.bot.copy_message(
                        chat_id=user,
                        from_chat_id=chat_id,
                        message_id=mess_id
                    )

                except Exception as e:
                    print(e)
                    continue

                finally:
                    await state.finish()

            await self.dp.bot.send_message(
                chat_id=chat_id,
                text=f"<b>Найдено пользователей:</b> {len(users)}\n\n",
                parse_mode="html"
            )

        else:
            async with state.proxy() as data:
                data["message_id"] = message.message_id

            await self.dp.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=chat_id,
                message_id=message.message_id
            )

            await self.dp.bot.send_message(
                chat_id=chat_id,
                text="Сообщение сохранено.\n\n"
                     "Отправьте /done, чтобы отправить рассылку или продолжите отправлять сообщение в очередь рассылки\n\n"
                     "/cancel - выйти"
            )


    async def admin_mailing_all_users(self, message: Message, state: FSMContext):
        tokens_and_users, users_count = self.admin_db.get_all_users()

        flag = False
        mailing_flag = True

        for token, users in tokens_and_users.items():
            text, audio_name, photo_name, video_name, video_note_name, document_name = await files_names(
                message=message, token=token, bot=self.bot
            )
            flag = any([text, audio_name, photo_name, video_name, video_note_name, document_name])

            if flag:
                if mailing_flag:
                    await self.dp.bot.send_message(
                        chat_id=message.chat.id,
                        text="🕑 Рассылка запущена!"
                    )
                    mailing_flag = False

                for user in users:
                    bot = Bot(token)

                    try:
                        if message.video:
                            await message.video.download(f"files/video/sending_video.mp4")
                            video_name = f"files/video/sending_video.mp4"

                            if message.caption:
                                text = message.html_text


                            else:
                                text = ""

                            with open(video_name, "rb") as video:
                                await bot.send_video(
                                    chat_id=user,
                                    video=video,
                                    caption=text + "\nСообщение от @customerlive_bot",
                                    parse_mode="html"
                                )

                        elif message.video_note:
                            await message.video.download(f"files/video/sending_video_note.mp4")
                            video_note_name = f"files/video/sending_video_note.mp4"

                            with open(video_note_name, "rb") as video_note:
                                await bot.send_animation(
                                    chat_id=user,
                                    animation=video_note,
                                    caption="Video"
                                )

                        elif message.photo:
                            photo = message.photo[-1]
                            photo_bytes = await photo.download("files/photo/sending.jpg")
                            photo_stream = open("files/photo/sending.jpg", "rb")
                            if message.caption:
                                await bot.send_photo(
                                    chat_id=user,
                                    photo=photo_stream.read(),
                                    caption=message.html_text + "\nСообщение от @customerlive_bot",
                                    parse_mode="html"
                                )

                            else:
                                await bot.send_photo(chat_id=user, photo=photo_stream.read())
                            photo_stream.close()

                        elif message.voice:
                            audio = message.voice
                            audio_bytes = await audio.download("files/voice/sending.ogg")
                            audio_stream = open("files/voice/sending.ogg", "rb")

                            await bot.send_audio(
                                chat_id=user, audio=audio_stream.read(),
                                caption="Сообщение от @customerlive_bot", title="Аудиосообщение",
                                performer="@customerlive_bot",
                            )
                            audio_stream.close()

                        elif message.document:
                            file = await self.bot.get_file(message.document.file_id)
                            file_path = file.file_path

                            if file_path.endswith(".pdf"):
                                await message.document.download(f"files/document/{token}document.pdf")
                                document_name = f"files/document/{token}document.pdf"

                                if message.caption:
                                    text = message.html_text

                                else:
                                    text = ""

                                with open(document_name, "rb") as file:
                                    await bot.send_document(
                                        chat_id=user,
                                        document=file,
                                        caption=text + "Сообщение от @customerlive_bot",
                                        parse_mode="html",
                                    )

                                os.remove(document_name)

                        elif message.text:
                            text = message.html_text

                            await bot.send_message(
                                chat_id=user,
                                text=text + "\nСообщение от @customerlive_bot",
                                parse_mode="html",
                                disable_web_page_preview=True
                            )

                    except Exception as e:
                        print(e)
                        continue

                    finally:
                        await state.finish()
            else:
                break

        if flag:
            await self.bot.send_message(
                chat_id=message.chat.id,
                text=f"Рассылка была сделана на количество юзеров: {users_count}"
            )


        else:
            await self.bot.send_message(
                chat_id=message.chat.id,
                text=f"Недопустимый формат!\n\n"
                     f"Доступные форматы:\n" \
                     f"1) Текст (поддерживается форматирование)\n" \
                     f"2) Фото\n" \
                     f"3) Фото с текстом\n" \
                     f"4) Голосовое сообщение\n" \
                     f"5) Видео\n" \
                     f"6) Видеосообщение\n" \
                     f"7) PDF-файлы\n\n"
            )


    async def add_command_state_handler(self, message: Message, state: FSMContext):
        chat = message.chat.id
        message_text = message.text

        async with state.proxy() as data:
            token = data["token"]

        commands_list = self.db.get_commands_list(bot_token=token)


        if message_text not in commands_list:
            async with state.proxy() as data:
                data["title"] = message_text

            text = "Введите автоответ для команды\n\n" \
                   "Доступные форматы:\n" \
                   "1) Текст (поддерживается форматирование)\n" \
                   "2) Фото\n" \
                   "3) Фото с текстом\n" \
                   "4) Голосовое сообщение\n" \
                   "5) Видео\n" \
                   "6) Видеосообщение\n" \
                   "7) PDF-файлы\n\n" \
                   "Или вернитесь к настройкам бота"

            await BotStates.add_description.set()
            await self.dp.bot.send_message(
                chat_id=chat,
                text=text,
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(
                        text="Вернуться к автоответам", callback_data="autoanswers"
                    )
                )
            )

        else:
            await message.answer(
                text="Данная команда уже создана, выберите другую или вернитесь к настройкам",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(
                        text="Вернуться к автоответам", callback_data="autoanswers"
                    )
                )
            )

    async def add_description_state_handler(self, message: Message, state: FSMContext):
        chat = message.chat.id

        async with state.proxy() as data:
            title = data["title"]
            token = data["token"]
            data["message_with_data"] = message
            data["mode"] = "command"

            text, audio_name, photo_name, video_name, video_note_name, document_name = await files_names(
                message=message, token=token, bot=self.bot
            )
            flag = any([text, audio_name, photo_name, video_name, video_note_name, document_name])
            # print("i'm here")

            if len(text) > 800:
                await self.bot.send_message(
                    chat_id=chat,
                    text="Длина сообщения должна не превышать 800 символов, попробуйте снова или вернитесь к настройкам",
                    reply_markup=back_to_admin_markup
                )

            elif flag:
                await BotStates.add_markup.set()

                text = "Теперь настроим кнопки:\n\n" \
                       "Чтобы добавить кнопки пришлите их в формате:\n" \
                       "text - url\n" \
                       "text2 - url && text3 - url\n\n" \
                       "text - надпись кнопки url - ссылка\n" \
                       "'-' - разделитель\n" \
                       "'&&' - склеить в строку\n\n" \
                       "url может быть ссылкой на другой автоответ бота или ссылкой на сайт\n\n" \
                       "ЕСЛИ НЕ НУЖНЫ КНОПКИ ОТПРАВЬ 0\n" \
                       "Кнопки обязательно должны быть через ' - ' с пробелами!"

                await self.bot.send_message(
                    chat_id=chat,
                    text=text,
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton(
                            text="Вернуться к настройкам бота", callback_data="back-to-admin"
                        )
                    )
                )

            else:
                text = "Неверный формат, попробуйте снова\n\n" \
                       "Доступные форматы:\n" \
                       "1) Текст (поддерживается форматирование)\n" \
                       "2) Фото\n" \
                       "3) Фото с текстом\n" \
                       "4) Голосовое сообщение\n" \
                       "5) Видео\n" \
                       "6) Видеосообщение\n" \
                       "7) PDF-файлы\n\n" \
                       "Или вернитесь к настройкам бота"

                await self.bot.send_message(
                    chat_id=chat,
                    text=text,
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton(
                            text="Вернуться к настройкам бота", callback_data="back-to-admin"
                        )
                    )
                )



    async def choose_command_state_handler(self, message: Message, state: FSMContext):
        chat = message.chat.id
        text = message.html_text

        async with state.proxy() as data:
            token = data["token"]
            command_mode = data["command_mode"]
            self.full_commands = self.db.get_commands_list(bot_token=token)

            if text in self.full_commands:
                data["title"] = text

                await BotStates.edit_text_command.set()

                if command_mode == "autoanswer":
                    message_text = "Доступные форматы:\n" \
                           "1) Текст (поддерживается форматирование)\n" \
                           "2) Фото\n" \
                           "3) Фото с текстом\n" \
                           "4) Голосовое сообщение\n" \
                           "5) Видео\n" \
                           "6) Видеосообщение\n" \
                           "7) PDF-файлы"

                    text = f"Выбрана команда: <i>{text}</i>\n" \
                           f"Введите новый автоответ для команды.\n\n"

                    text = text + message_text
                    callback_data = "edit-text-command"

                elif command_mode == "command":
                    text = f"Выбрана команда: <i>{text}</i>\n" \
                           f"Введите новое название команды.\n\n"
                    callback_data = "edit-command"

                instruction_message = await self.dp.bot.send_message(
                        chat_id=chat,
                        text=text,
                        parse_mode="html",
                        reply_markup=InlineKeyboardMarkup().add(
                            InlineKeyboardButton(text="Назад", callback_data=callback_data)
                        )
                    )

                async with state.proxy() as data:
                    data["instruction_message_id"] = instruction_message.message_id

            else:
                await self.dp.bot.send_message(
                    chat_id=chat,
                    text="Нет такой команды",
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton(text="Назад", callback_data="autoanswers")
                    )
                )

    async def edit_command_state_handler(self, message: Message, state: FSMContext):
        chat = message.chat.id

        async with state.proxy() as data:
            title = data["title"]
            token = data["token"]
            command_mode = data["command_mode"]

            if command_mode == "autoanswer":
                text, audio_name, photo_name, video_name, video_note_name, document_name = await files_names(
                    message=message, token=token, bot=self.bot
                )
                flag = any([text, audio_name, photo_name, video_name, video_note_name, document_name])

                if len(text) > 800:
                    await self.bot.send_message(
                        chat_id=chat,
                        text="Длина сообщения должна не превышать 800 символов, попробуйте снова или вернитесь к настройкам",
                        reply_markup=back_to_admin_markup
                    )

                elif flag:
                    async with state.proxy() as data:
                        data["mode"] = "command"
                        data["message_with_data"] = message

                    await BotStates.add_markup.set()

                    text = "Теперь настроим кнопки:\n\n" \
                           "Чтобы добавить кнопки пришлите их в формате:\n" \
                           "text - url\n" \
                           "text2 - url && text3 - url\n\n" \
                           "text - надпись кнопки url - ссылка\n" \
                           "'-' - разделитель\n" \
                           "'&&' - склеить в строку\n\n" \
                           "url может быть ссылкой на другой автоответ бота или ссылкой на сайт\n\n" \
                           "ЕСЛИ НЕ НУЖНЫ КНОПКИ ОТПРАВЬ 0\n" \
                           "Кнопки обязательно должны быть через ' - ' с пробелами!"

                    await self.bot.send_message(
                        chat_id=chat,
                        text=text,
                        reply_markup=InlineKeyboardMarkup().add(
                            InlineKeyboardButton(
                                text="Вернуться к настройкам бота", callback_data="back-to-admin"
                            )
                        )
                    )
                    # self.db.add_command_with_description(
                    #     bot_token=token,
                    #     title=title,
                    #     description=text,
                    #     audio_name=audio_name,
                    #     photo_name=photo_name,
                    #     video_name=video_name,
                    #     video_note_name=video_note_name,
                    #     document_name=document_name
                    # )
                    #
                    # commands_dict = self.db.get_commands_with_descriptions(bot_token=token)
                    # for command in commands_dict:
                    #     if command == title:
                    #         description, audio, photo, video, video_note, document = commands_dict[command]
                    #         sending_message = await sending_function(
                    #             bot=self.bot,
                    #             chat_id=chat,
                    #             text=description,
                    #             audio=audio,
                    #             photo=photo,
                    #             video=video,
                    #             video_note=video_note,
                    #             document=document
                    #         )
                    #         data["sending_message_id"] = sending_message.message_id
                    #         break
                    #
                    # data["user_message_id"] = message.message_id
                    #
                    #
                    # await self.bot.send_message(
                    #     chat_id=chat,
                    #     text=f"Теперь при вызове команды {title}, будет выводиться сообщение выше:",
                    #     reply_markup=InlineKeyboardMarkup().add(
                    #         InlineKeyboardButton(
                    #             text="Вернуться к настройкам бота", callback_data="back-to-admin"
                    #         )
                    #     )
                    # )

                else:
                    text = "Неверный формат, попробуйте снова\n\n" \
                           "Доступные форматы:\n" \
                           "1) Текст (поддерживается форматирование)\n" \
                           "2) Фото\n" \
                           "3) Фото с текстом\n" \
                           "4) Голосовое сообщение\n" \
                           "5) Видео\n" \
                           "6) Видеосообщение\n" \
                           "7) PDF-файлы\n\n" \
                           "Или вернитесь к настройкам бота"

                    await self.bot.send_message(
                        chat_id=chat,
                        text=text,
                        reply_markup=InlineKeyboardMarkup().add(
                            InlineKeyboardButton(
                                text="Вернуться к настройкам бота", callback_data="back-to-admin"
                            )
                        )
                    )

            elif command_mode == "command":
                if message.text in self.db.get_commands_list(bot_token=token):
                    await self.bot.send_message(
                        chat_id=chat,
                        text="Нельзя изменить команду на существующую.\n"
                             "Введите новую команду или вернитесь к настройкам автоответов",
                        parse_mode="html",
                        reply_markup=InlineKeyboardMarkup().add(
                            InlineKeyboardButton(
                                text="Вернуться к настройкам автоответов", callback_data="autoanswers"
                            )
                        )
                    )

                elif message.text is not None:
                    self.db.update_command_name(
                        bot_token=token, prev_name=title, new_name=message.text
                    )

                    await self.bot.send_message(
                        chat_id=chat,
                        text=f"Команда <i>{title}</i> успешно заменена на <b>{message.text}</b>\n"
                             f"Теперь при вызове команды: <b>{message.text}</b> будет выводится автоответ, который был у команды <i>{title}</i>",
                        parse_mode="html",
                        reply_markup=InlineKeyboardMarkup().add(
                            InlineKeyboardButton(
                                text="Вернуться к настройкам автоответов", callback_data="autoanswers"
                            )
                        )
                    )

                else:
                    await self.bot.send_message(
                        chat_id=chat,
                        text=f"Недопустимый формат, команда должна быть текстом,"
                             f"введите команду снова или вернитесь к настройкам автоответов",
                        parse_mode="html",
                        reply_markup=InlineKeyboardMarkup().add(
                            InlineKeyboardButton(
                                text="Вернуться к настройкам автоответов", callback_data="autoanswers"
                            )
                        )
                    )

    async def edit_start_message(self, message: Message, state: FSMContext):
        chat = message.chat.id
        # print(message)

        if message.text == "/start":
            await self.start_handler(message=message, state=state)
        async with state.proxy() as data:
            token = data["token"]
            data["message_with_data"] = message
            data["mode"] = "start"

            loading_message = await self.bot.send_message(
                chat_id=chat,
                text=loading_text
            )

            text, audio_name, photo_name, video_name, video_note_name, document_name = await files_names(message=message, token=token, bot=self.bot)
            flag = any([text, audio_name, photo_name, video_name, video_note_name, document_name])
            if len(text) > 800:
                await self.bot.send_message(
                    chat_id=chat,
                    text="Длина сообщения должна не превышать 800 символов, попробуйте снова или вернитесь к настройкам",
                    reply_markup=back_to_admin_markup
                )
                await self.bot.delete_message(
                    chat_id=chat,
                    message_id=loading_message.message_id
                )

            elif flag:
                await self.bot.delete_message(
                    chat_id=chat,
                    message_id=loading_message.message_id
                )
                await BotStates.add_markup.set()
                text = "Теперь настроим кнопки:\n\n" \
                       "Чтобы добавить кнопки пришлите их в формате:\n" \
                       "text - url\n" \
                       "text2 - url && text3 - url\n\n" \
                       "text - надпись кнопки url - ссылка\n" \
                       "'-' - разделитель\n" \
                       "'&&' - склеить в строку\n\n" \
                       "url может быть ссылкой на другой автоответ бота или ссылкой на сайт\n\n" \
                       "ЕСЛИ НЕ НУЖНЫ КНОПКИ ОТПРАВЬ 0\n" \
                       "Кнопки обязательно должны быть через ' - ' с пробелами!"

                await self.bot.send_message(
                    chat_id=chat,
                    text=text,
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton(
                            text="Вернуться к настройкам бота", callback_data="back-to-admin"
                        )
                    )
                )
                # self.db.start_message(
                #     method="save",
                #     bot_token=token,
                #     text=text,
                #     audio_name=audio_name,
                #     photo_name=photo_name,
                #     video_name=video_name,
                #     video_note_name=video_note_name,
                #     document_name=document_name
                # )
                #
                # greeting, audio, photo, video, video_note, document = self.db.start_message(method="get", bot_token=token)
                #
                # sending_message = await sending_function(
                #     bot=self.bot,
                #     chat_id=chat,
                #     text=greeting,
                #     audio=audio,
                #     photo=photo,
                #     video=video,
                #     video_note=video_note,
                #     document=document
                # )
                #
                # data["user_message_id"] = message.message_id
                # data["sending_message_id"] = sending_message.message_id
                #
                # await self.bot.send_message(
                #         chat_id=chat,
                #         text="Установлено новое стартовое сообщение!",
                #         reply_markup=InlineKeyboardMarkup().add(
                #             InlineKeyboardButton(
                #                 text="Вернуться к настройкам бота", callback_data="back-to-admin"
                #             )
                #         )
                #     )

            else:
                text = "Неверный формат, попробуйте отправить сообщение снова\n\n" \
                       "Доступные форматы:\n" \
                       "1) Текст (поддерживается форматирование)\n" \
                       "2) Фото\n" \
                       "3) Фото с текстом\n" \
                       "4) Голосовое сообщение\n" \
                       "5) Видео\n" \
                       "6) Видеосообщение\n" \
                       "7) PDF-файлы\n\n" \
                       "Или вернитесь обратно к настройкам"

                await self.bot.send_message(
                    chat_id=chat,
                    text=text,
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton(
                            text="Вернуться к настройкам бота", callback_data="back-to-admin"
                        )
                    )
                )






    async def delete_command_state_handler(self, message: Message, state: FSMContext):
        chat = message.chat.id
        text = message.text

        async with state.proxy() as data:
            token = data["token"]

            commands_list = self.db.get_commands_list(bot_token=token)

            if text in commands_list:
                self.db.delete_command(command=text, bot_token=token)
                # print(message.text, self.full_commands)
                sending_message = await self.dp.bot.send_message(
                    chat_id=chat,
                    text=f"Команда <i>{text}</i>  успешно удалена",
                    parse_mode="html",
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton(
                            text="Вернуться к автоответам", callback_data="autoanswers"
                        )
                    )
                )
                data["sending_message_id"] = sending_message.message_id

                await BotStates.bot_settings.set()

            else:
                sending_message = await self.dp.bot.send_message(
                    chat_id=chat,
                    text="Нет такой команды.",
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton(
                            text="Вернуться к настройкам бота", callback_data="back-to-admin"
                        )
                    )
                )
                data["sending_message_id"] = sending_message.message_id

    async def add_application_text(self, message: Message, state: FSMContext):
        chat = message.chat.id
        text = message.text

        if len(text) <= 800:
            async with state.proxy() as data:
                data["application_text"] = message.html_text

            await BotStates.add_application_button.set()
            await self.bot.send_message(
                chat_id=chat,
                text="Назовите кнопку, данный текст будет виден пользователям, ограничения - 15 символов",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="Вернуться к настройкам бота", callback_data="back-to-admin")
                )
            )

        elif len(text) > 800:
            await self.bot.send_message(
                chat_id=chat,
                text="Текст не должен превышать 800 символов, попробуйте ещё раз или вернитесь к настройкам бота",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="Вернуться к настройкам бота", callback_data="back-to-admin")
                )
            )

    async def add_application_button(self, message: Message, state: FSMContext):
        chat = message.chat.id
        text = message.text

        if len(text) <= 15:
            async with state.proxy() as data:
                data["application_button"] = text

            await BotStates.add_application_name.set()
            await self.bot.send_message(
                chat_id=chat,
                text="Назовите заявку, это название будет видеть менеджер, когда клиент оставит заявку, ограничение - 25 символов",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="Вернуться к настройкам бота", callback_data="back-to-admin")
                )
            )

        elif len(text) > 15:
            await self.bot.send_message(
                chat_id=chat,
                text="Текст не должен превышать 15 символов, попробуйте ещё раз или вернитесь к настройкам бота",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="Вернуться к настройкам бота", callback_data="back-to-admin")
                )
            )


    async def add_application_name(self, message: Message, state: FSMContext):
        chat = message.chat.id
        text = message.text

        if " " not in text and len(text) <= 25:
            async with state.proxy() as data:
                loading_message = await self.bot.send_message(
                    chat_id=chat,
                    text=loading_text
                )

                await self.add_info(chat, state, application_name=text, LMI=loading_message.message_id)


        else:
            await self.bot.send_message(
                chat_id=chat,
                text="Название заявки не должно превышать 25 символов и содержать пробелы, попробуйте снова, откажитесь от заявки или вернитесь к настройкам бота",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(
                        text="Не делать заявку",
                        callback_data="don't_add_application"
                    )
                ).add(
                        InlineKeyboardButton(
                            text="Вернуться к настройкам бота",
                            callback_data="back-to-admin"
                        )
                    )
                )


        

    async def add_info(self, chat, state, application_name=None, LMI=None):
        async with state.proxy() as data:
            token = data["token"]
            mode = data["mode"]
            message_with_data = data["message_with_data"]
            markup_text = data["markup_text"]
            application_text = data.get("application_text")
            application_button = data.get("application_button")
            # print(message_with_data.document)
        commands_list = self.db.get_commands_list(bot_token=token)
        markup = InlineKeyboardMarkup()

        loading_message = await self.bot.send_message(
            chat_id=chat,
            text=loading_text
        )

        if LMI is not None:
            await self.bot.delete_message(
                chat_id=chat,
                message_id=LMI
            )

        if mode == "start":
            text, audio_name, photo_name, video_name, video_note_name, document_name = await files_names(
                message=message_with_data, token=token, bot=self.bot)

            self.db.start_message(
                method="save",
                bot_token=token,
                text=text,
                audio_name=audio_name,
                photo_name=photo_name,
                video_name=video_name,
                video_note_name=video_note_name,
                document_name=document_name,
                markup_text=markup_text,
                application_text=application_text,
                application_button=application_button,
                application_name=application_name
            )

            greeting, audio, photo, video, video_note, document, document_name, markup_text, application_text, application_button, application_name = self.db.start_message(
                method="get",
                bot_token=token
            )

            if application_button is None:
                application_button = "Оставить заявку"

            if application_name is not None:
                markup.add(
                    InlineKeyboardButton(
                        text=application_button, callback_data=application_name
                    )
                )

            if markup_text != "0":
                markup = create_markup(markup_text=markup_text, markup=markup, commands_list=commands_list)
            sending_message = await sending_function(
                bot=self.bot,
                chat_id=chat,
                text=greeting,
                audio=audio,
                photo=photo,
                video=video,
                video_note=video_note,
                document=document,
                document_name=document_name,
                markup=markup
            )

            async with state.proxy() as data:
                data["user_message_id"] = message_with_data.message_id
                data["sending_message_id"] = sending_message.message_id

            await BotStates.bot_settings.set()

            await self.bot.delete_message(
                chat_id=chat,
                message_id=loading_message.message_id
            )

            await self.bot.send_message(
                chat_id=chat,
                text="Установлено новое стартовое сообщение!",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(
                        text="Вернуться к настройкам бота", callback_data="back-to-admin"
                    )
                )
            )

        elif mode == "command":
            title = data["title"]
            text, audio_name, photo_name, video_name, video_note_name, document_name = await files_names(
                message=message_with_data, token=token, bot=self.bot
            )

            self.db.add_command_with_description(
                bot_token=token,
                title=title,
                description=text,
                audio_name=audio_name,
                photo_name=photo_name,
                video_name=video_name,
                video_note_name=video_note_name,
                document_name=document_name,
                markup_text=markup_text,
                application_text=application_text,
                application_button=application_button,
                application_name=application_name
            )

            if application_button is None:
                application_button = "Оставить заявку"

            if application_name is not None:
                markup.add(
                    InlineKeyboardButton(
                        text=application_button, callback_data=application_name.replace(" ", "%")
                    )
                )

            if markup_text != "0":
                markup = create_markup(markup_text=markup_text, markup=markup, commands_list=commands_list)
            commands_dict = self.db.get_commands_with_descriptions(bot_token=token)
            for command in commands_dict:
                if command == title:
                    description, audio, photo, video, video_note, document, document_name, markup_text, application_text, application_button, application_name = commands_dict[command]
                    sending_message = await sending_function(
                        bot=self.bot,
                        chat_id=chat,
                        text=description,
                        audio=audio,
                        photo=photo,
                        video=video,
                        video_note=video_note,
                        document=document,
                        document_name=document_name,
                        markup=markup
                    )

                    break

            async with state.proxy() as data:
                try:
                    data["sending_message_id"] = sending_message.message_id
                except Exception as e:
                    print(e, 1988)
                data["user_message_id"] = message_with_data.message_id

            await BotStates.bot_settings.set()

            await self.bot.delete_message(
                chat_id=chat,
                message_id=loading_message.message_id
            )

            await self.bot.send_message(
                chat_id=chat,
                text=f"Теперь при вызове команды {title}, будет выводиться сообщение выше:",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(
                        text="Вернуться к настройкам бота", callback_data="back-to-admin"
                    )
                )
            )

        elif mode == "add_step":
            async with state.proxy() as data:
                token = data["token"]
                username = data["username"]
                time = data["time"]

                hours, minutes = list(map(int, time.split('/')))
                only_minutes = hours * 60 + minutes

                text, audio_name, photo_name, video_name, video_note_name, document_name = await files_names(
                    message=message_with_data, token=token, bot=self.bot
                )

                self.funnel_db.add_step(
                    tg_id=chat, token=token, step=text, minutes=only_minutes,
                    audio_name=audio_name, photo_name=photo_name,
                    video_name=video_name, video_note_name=video_note_name,
                    document_name=document_name, markup_text=markup_text,
                    application_text=application_text,
                    application_button=application_button,
                    application_name=application_name
                )

                await self.bot.send_message(
                    chat_id=chat,
                    text=f"Теперь через это количество часов и минут: {hours}/{minutes} после срабатывания триггера будет отправляться этот шаг"
                )

            await self.bot.delete_message(
                chat_id=chat,
                message_id=loading_message.message_id
            )

            await BotStates.bot_settings.set()
            bot_info = await Bot(token).me
            is_trigger = self.funnel_db.get_trigger(token=token)

            if is_trigger is None:
                trigger_text = "\nДля настройки автоворонки установите триггер"

            else:
                trigger_text = f"\nУстановлен триггер: {is_trigger}"

            await FunnelStates.funnel_steps.set()
            await self.bot.send_message(
                chat_id=chat,
                text=f"Настройка воронки @{bot_info.username}" + trigger_text,
                reply_markup=funnel_steps_markup,
            )

    async def add_markup(self, message: Message, state: FSMContext):
        text = message.text
        tg_id = message.from_user.id
        # print(message)
        # print(text)
        if " - " in text or text == "0":
            async with state.proxy() as data:
                data["markup_text"] = text

            await self.bot.send_message(
                chat_id=tg_id,
                text="Кнопки были настроены\n\n"
                     "Добавить кнопку заявки?",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(
                        text="Да", callback_data="add_application"
                    )
                ).add(InlineKeyboardButton(
                    text="Нет", callback_data="don't_add_application"
                ))
            )

        else:
            await self.bot.send_message(
                chat_id=tg_id,
                text="Кнопки обязательно должны быть через ' - ' с пробелами!"
            )


    async def add_trigger_handler(self, message: Message, state: FSMContext):
        tg_id = message.from_user.id
        text = message.text

        async with state.proxy() as data:
            token = data["token"]
            self.funnel_db.add_trigger(tg_id=tg_id, token=token, trigger=text)
        bot_info = await Bot(token).me
        await FunnelStates.funnel_steps.set()

        await self.bot.send_message(
            chat_id=tg_id,
            text=f"Установлен новый триггер: {text}"
        )

        await self.bot.send_message(
            chat_id=tg_id,
            text=f"Настройка воронки бота: @{bot_info.username}",
            reply_markup=funnel_steps_markup,
        )


    async def add_step_handler(self, message: Message, state: FSMContext):
        tg_id = message.from_user.id
        chat = message.from_user.id
        async with state.proxy() as data:
            token = data["token"]

        loading_message = await self.bot.send_message(
            chat_id=tg_id,
            text=loading_text
        )

        text, audio_name, photo_name, video_name, video_note_name, document_name = await files_names(
            message=message, token=token, bot=self.bot
        )

        flag = any([text, audio_name, photo_name, video_name, video_note_name, document_name])

        if len(text) > 800:
            await self.bot.send_message(
                chat_id=chat,
                text="Длина сообщения должна не превышать 800 символов, попробуйте снова или вернитесь к настройкам",
                reply_markup=back_to_funnel_settings
            )

            await self.bot.delete_message(
                chat_id=chat,
                message_id=loading_message.message_id
            )

        elif flag:
            async with state.proxy() as data:
                data["message_with_data"] = message
                # data["photo_name"] = photo_name
                # data["step"] = text
                # data["video_name"] = video_name
                # data["video_note_name"] = video_note_name
                # data["audio_name"] = audio_name
                # data["document_name"] = document_name

            await FunnelStates.add_time.set()
            text = "Теперь укажите время, через которое должно отправляться сообщение после срабатывания триггера\n\n" \
                   "ВАЖНО: сообщение должно быть в формате часы/минуты, обязательно через /\n" \
                   "Примеры:\n" \
                   "<pre>0/1</pre> – пользователь получит сообщение через 1 минуту после срабатывания триггера\n" \
                   "<pre>0/40</pre> - пользователь получит сообщение через 40 минут после отправки триггера\n" \
                   "<pre>1/0</pre> - пользователь получит сообщение через 1 час после отправки триггера\n" \
                   "<pre>3/15</pre> – пользователь получит сообщение через 3 часа 15 минут, после отправки триггера\n" \
                   "<pre>42/0</pre> – пользователь получит сообщение через 42 часа, после отправки триггера\n"

            await self.bot.delete_message(
                chat_id=tg_id,
                message_id=loading_message.message_id
            )

            await self.bot.send_message(
                chat_id=tg_id,
                text=text,
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="Назад к настройке воронки", callback_data="funnel-settings")
                ),
                parse_mode="html"
            )

        else:
            await self.bot.send_message(
                chat_id=tg_id,
                text="Неверный формат, попробуйте отправить сообщение снова.\n\n"
                     "Поддерживаемые форматы: текст, фото, фото с текстом, аудио, видео, видеосообщение-кружок, голосовое сообщение, pdf-файл и pdf-файл с подписью\n\n"
                     "Или вернитесь в меню настроек"
            )

            await self.bot.delete_message(
                chat_id=tg_id,
                message_id=loading_message.message_id
            )

    async def add_time_handler(self, message: Message, state: FSMContext):
        tg_id = message.from_user.id
        print("time_handler", message)
        if message.text == "/start":
            await self.start_handler(message, state)

        elif message.text:
            text = message.text

            loading_message = await self.bot.send_message(
                chat_id=tg_id,
                text=loading_text
            )


            try:
                hours, minutes = list(map(int, text.split('/')))
                only_minutes = hours * 60 + minutes

                async with state.proxy() as data:
                    data["mode"] = "add_step"
                    data["time"] = text

                await BotStates.add_markup.set()
                text = "Теперь настроим кнопки:\n\n" \
                       "Чтобы добавить кнопки пришлите их в формате:\n" \
                       "text - url\n" \
                       "text2 - url && text3 - url\n\n" \
                       "text - надпись кнопки url - ссылка\n" \
                       "'-' - разделитель\n" \
                       "'&&' - склеить в строку\n\n" \
                       "url может быть ссылкой на другой автоответ бота или ссылкой на сайт\n\n" \
                       "ЕСЛИ НЕ НУЖНЫ КНОПКИ ОТПРАВЬ 0"

                await self.bot.send_message(
                    chat_id=tg_id,
                    text=text,
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton(
                            text="Вернуться к настройкам бота", callback_data="back-to-admin"
                        )
                    )
                )

            except Exception as e:
                print(e, "error")
                await self.bot.send_message(
                    chat_id=tg_id,
                    text="Время должно быть в формате часы/минуты",
                )

            finally:
                await self.bot.delete_message(
                    chat_id=tg_id,
                    message_id=loading_message.message_id
                )

            #     await state.finish()
            #     await FunnelStates.funnel_steps.set()
            #     async with state.proxy() as data:
            #         data["token"] = token
            #         data["username"] = username
        else:
            await self.bot.send_message(
                chat_id=tg_id,
                text="Время должно быть в формате часы/минуты",
            )

    async def text_handler(self, message: Message, state: FSMContext):
        text = message.text
        print(message)

    async def add_bot_state(self, message: Message, state: FSMContext):
        text = message.text
        tg_id = message.from_user.id
        mess_id = message.message_id
        menu = InlineKeyboardMarkup().add(InlineKeyboardButton(text="Вернуться в меню", callback_data="back-to-menu"))

        if message.text == "/start":
            await self.start_handler(message, state)

        elif text[:10].isdigit() and text[10] == ":":
            loading_message = await self.bot.send_message(
                chat_id=tg_id,
                text=loading_text
            )

            try:
                tokens = self.db.get_tokens()

                if tokens is None or text not in tokens:
                    self.db.add_bot(
                        tg_id=tg_id,
                        bot_token=text
                    )

                    self.db.start_message(
                        method="save",
                        bot_token=text,
                        text="Стартовое сообщение"
                    )

                    # self.funnel_db.add_funnel(
                    #     token=text,
                    #     tg_id=tg_id
                    # )

                    async with state.proxy() as data:
                        try:
                            await self.bot.delete_message(
                                chat_id=tg_id,
                                message_id=data["message_id"]
                            )
                        except Exception:
                            pass

                        try:
                            await self.bot.delete_message(
                                chat_id=tg_id,
                                message_id=data["token_is_used"]
                            )
                        except Exception:
                            pass

                        try:
                            await self.bot.delete_message(
                                chat_id=tg_id,
                                message_id=data["incorrect_token"]
                            )
                        except Exception:
                            pass

                        try:
                            await self.bot.delete_message(
                                chat_id=tg_id,
                                message_id=data["used_token_message"]
                            )
                        except Exception:
                            pass

                    await self.bot.delete_message(
                        chat_id=tg_id,
                        message_id=mess_id
                    )

                    async with state.proxy() as data:
                        data["token"] = text

                    bot_info = await Bot(token=text).me

                    await AddBotStates.step_1.set()
                    text = f"Выбранный бот: @{bot_info.username}\n\n" \
                           f"Теперь давайте настроим вашего бота\n" \
                           f"1. Создайте новый канал, выберите тип канала “приватный”\n" \
                           f"2. Добавьте созданного бота в канал\n" \
                           f"3. Назначьте созданного бота администратором\n\n" \
                           f"В этом канале будет храниться переписка с пользователями, где вы сможете посмотреть диалог с конкретным клиентом.\n\n" \
                           f"После выполнения этих действий нажмите на кнопку ниже"

                    await self.bot.delete_message(
                        chat_id=tg_id,
                        message_id=loading_message.message_id
                    )

                    step_1_message = await self.bot.send_message(
                        chat_id=tg_id,
                        text=text,
                        reply_markup=InlineKeyboardMarkup().add(
                            InlineKeyboardButton(text="Далее >>>", callback_data="to-2-step")
                        )
                    )

                    async with state.proxy() as data:
                        data["step_1"] = step_1_message.message_id
                        # data["bot_added_message"] = bot_added_message.message_id

                else:
                    token_is_used = await self.bot.send_message(
                        chat_id=tg_id,
                        text="Данный токен уже используется",
                        reply_markup=menu
                    )

                    async with state.proxy() as data:
                        data["used_token_message"] = message.message_id
                        data["token_is_used"] = token_is_used.message_id
                        #print(data)

                    await self.bot.delete_message(
                        chat_id=tg_id,
                        message_id=loading_message.message_id
                    )

            except Exception as e:
                print(e)



        else:
            incorrect_token = await self.bot.send_message(
                chat_id=tg_id,
                text="Некорректный токен",
                reply_markup=menu
            )

            async with state.proxy() as data:
                data["incorrect_token"] = incorrect_token.message_id
                #print(data)

    async def admin_handler(self, message: Message, state: FSMContext):
        if message.from_user.id == 1283802964 or message.from_user.id == 84327932:
            await state.finish()
            await self.bot.send_message(
                chat_id=message.from_user.id,
                text="Админка",
                reply_markup=admin_actions_markup
            )

    def register_handler(self):
        self.dp.register_message_handler(callback=self.add_bot_state, state=AddBotStates.add_bot)
        self.dp.register_message_handler(callback=self.add_time_handler, content_types=ContentTypes.ANY, state=FunnelStates.add_time)
        self.dp.register_message_handler(callback=self.add_step_handler, content_types=ContentTypes.ANY, state=FunnelStates.add_step)
        self.dp.register_message_handler(callback=self.add_trigger_handler, content_types=ContentTypes.TEXT, state=FunnelStates.add_trigger)
        self.dp.register_callback_query_handler(callback=self.callback_handler, state="*")
        self.dp.register_message_handler(callback=self.add_markup, content_types=ContentTypes.TEXT, state=BotStates.add_markup)
        self.dp.register_message_handler(callback=self.add_application_text, content_types=ContentTypes.TEXT, state=BotStates.add_application_text)
        self.dp.register_message_handler(callback=self.add_application_button, content_types=ContentTypes.TEXT, state=BotStates.add_application_button)
        self.dp.register_message_handler(callback=self.add_application_name, state=BotStates.add_application_name, content_types=ContentTypes.TEXT)
        self.dp.register_message_handler(callback=self.add_command_state_handler, content_types=ContentTypes.TEXT,
                                         state=BotStates.add_command)
        self.dp.register_message_handler(callback=self.add_invite_link_handler, state=BotStates.add_invite_link, content_types=ContentTypes.TEXT)
        self.dp.register_message_handler(callback=self.add_description_state_handler, content_types=ContentTypes.ANY, state=BotStates.add_description)
        self.dp.register_message_handler(callback=self.choose_command_state_handler, content_types=ContentTypes.TEXT, state=BotStates.choose_command)
        self.dp.register_message_handler(callback=self.edit_command_state_handler, content_types=ContentTypes.ANY, state=BotStates.edit_text_command)
        self.dp.register_message_handler(callback=self.edit_start_message, content_types=ContentTypes.ANY, state=BotStates.edit_start_message),
        self.dp.register_message_handler(callback=self.delete_command_state_handler, content_types=ContentTypes.TEXT, state=BotStates.delete_command)
        self.dp.register_message_handler(callback=self.admin_mailing_all_users, content_types=ContentTypes.ANY, state=BotStates.admin_mailing_all_users)
        self.dp.register_message_handler(callback=self.mailing_state_handler, content_types=ContentTypes.ANY, state=BotStates.admin_mailing_to_admins)
        self.dp.register_message_handler(callback=self.start_handler, commands=["start"], state="*")
        self.dp.register_message_handler(callback=self.admin_handler, commands=["admin"], state="*")
        self.dp.register_message_handler(callback=self.text_handler, content_types=ContentTypes.TEXT)


    def run(self):
        self.register_handler()
        executor.start_polling(dispatcher=self.dp, skip_updates=True)


if __name__ == "__main__":
    botik = LivegramBot()
    botik.run()