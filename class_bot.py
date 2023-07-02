from aiogram import Bot, Dispatcher
from aiogram.types import ContentTypes, Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import IsReplyFilter
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import BotBlocked

from utils.db_api.database import Database
from utils.db_api.funnel_db import FunnelDatabase
from markups.admin_markup import admin_markup
from markups.back_markups import back_to_admin_markup

from handlers.bot_states import BotStates
from aiogram.utils.exceptions import BadRequest
from datetime import datetime


class MyBot:
    def __init__(self, token: str, database_name: str):
        memory = MemoryStorage()
        self.bot_token = token
        self.bot = Bot(token=token)
        self.dp = Dispatcher(self.bot, storage=memory)
        self.db = Database(name=database_name)
        self.funnel_db = FunnelDatabase(name="funnels.db")

        self.chat_link = self.db.get_chat_link(bot_token=self.bot_token)
        self.group_id = self.db.get_group_id(bot_token=self.bot_token)


        self.full_commands = self.db.get_commands_list(bot_token=self.bot_token)


    async def start_handler(self, message: Message):
        users = self.db.get_users(bot_token=self.bot_token)
        tg_id = message.from_user.id
        chat = message.chat.id
        username = message.from_user.username
        text = message.text
        funnel_text = message.html_text

        self.trigger = self.funnel_db.get_trigger(token=self.bot_token)
        self.funnel_users = self.funnel_db.get_users(token=self.bot_token)
        self.funnel_users = [user[0] for user in self.funnel_users]

        if funnel_text is not None and funnel_text[0] == "/":
            funnel_text = funnel_text[1:]

        if self.trigger is not None and tg_id not in self.funnel_users and self.trigger.lower() == funnel_text.lower():
            self.funnel_db.add_or_update_user(token=self.bot_token, tg_id=tg_id, trigger_time=f"{datetime.now().hour} {datetime.now().day}")

        await self.dp.bot.send_message(
            chat_id=chat,
            text=self.db.start_message(method="get", bot_token=self.bot_token),
            parse_mode="html"
        )
        if tg_id not in users:
            try:
                await self.dp.bot.send_message(
                    chat_id=self.chat_link, text=f"Чат с пользователем @{username}",
                )

                reply_message = await self.dp.bot.send_message(
                    chat_id=self.group_id,
                    text="Новый чат",
                )
                self.db.add_user_post(tg_id=tg_id, post_id=reply_message.message_id + 1, bot_token=self.bot_token)

            except Exception as e:
                print(e)

    async def text_handler(self, message: Message, state: FSMContext):
        tg_id = message.from_user.id
        m_id = message.message_id
        text = message.html_text
        chat_type = message.chat.type
        funnel_text = message.html_text

        self.trigger = self.funnel_db.get_trigger(token=self.bot_token)
        self.funnel_users = self.funnel_db.get_users(token=self.bot_token)
        self.funnel_users = [user[0] for user in self.funnel_users]

        if funnel_text is not None and funnel_text[0] == "/":
            funnel_text = funnel_text[1:]

        if self.trigger is not None and tg_id not in self.funnel_users and self.trigger.lower() == funnel_text.lower():
            self.funnel_db.add_or_update_user(token=self.bot_token, tg_id=tg_id,
                                              trigger_time=f"{datetime.now().hour} {datetime.now().day}")

        if message.chat.id == self.group_id and text != "/set_group":
            await self.admin_message_handler(message=message)

        elif text is not None and text[0] == "/" and text[1:] in self.full_commands:
            await self.commands(message=message, state=state)

        elif chat_type == "private":
            try:
                message_to_chat = await self.dp.bot.copy_message(
                    chat_id=self.group_id,
                    from_chat_id=tg_id,
                    message_id=m_id,
                    reply_to_message_id=self.db.get_post_id(tg_id=tg_id, bot_token=self.bot_token)
                )
                self.db.add_user_message(tg_id=tg_id, message_id=message_to_chat.message_id, bot_token=self.bot_token)

            except BadRequest:
                pass

            except Exception as e:
                pass

        elif chat_type == "supergroup" and text == "/set_group":
            sender_chat = message.sender_chat

            if sender_chat is not None and sender_chat.type == "channel":
                group = message.chat.id
                channel = sender_chat.id
                self.db.set_group_to_bot(
                    bot_token=self.bot_token,
                    channel_id=channel,
                    group_id=group
                )
                self.chat_link = self.db.get_chat_link(bot_token=self.bot_token)
                self.group_id = self.db.get_group_id(bot_token=self.bot_token)

                await self.dp.bot.send_message(
                    chat_id=message.chat.id,
                    text="Настройка прошла успешно"
                )

    async def commands(self, message: Message, state: FSMContext):
        tg_id = message.from_user.id
        m_id = message.message_id
        commands_dict = self.db.get_commands_with_descriptions(bot_token=self.bot_token)
        funnel_text = message.html_text

        self.trigger = self.funnel_db.get_trigger(token=self.bot_token)
        self.funnel_users = self.funnel_db.get_users(token=self.bot_token)
        self.funnel_users = [user[0] for user in self.funnel_users]

        if funnel_text is not None and funnel_text[0] == "/":
            funnel_text = funnel_text[1:]

        if self.trigger is not None and tg_id not in self.funnel_users and self.trigger.lower() == funnel_text.lower():
            self.funnel_db.add_or_update_user(token=self.bot_token, tg_id=tg_id,
                                              trigger_time=f"{datetime.now().hour} {datetime.now().day}")

        message_to_chat = await self.dp.bot.copy_message(
            chat_id=self.group_id,
            from_chat_id=tg_id,
            message_id=m_id,
            reply_to_message_id=self.db.get_post_id(tg_id=tg_id, bot_token=self.bot_token)
        )

        self.db.add_user_message(tg_id=tg_id, message_id=message_to_chat.message_id, bot_token=self.bot_token)
        await self.dp.bot.send_message(
            chat_id=tg_id,
            text=commands_dict[message.text[1:]],
            parse_mode="html",
        )


    async def admin_message_handler(self, message: Message):
        chat_type = message.chat.type
        #print(message)
        if chat_type == "supergroup":
            try:
                if message.sender_chat is None or message.sender_chat.type != "channel":
                    await self.dp.bot.copy_message(
                        from_chat_id=message.chat.id,
                        message_id=message.message_id,
                        chat_id=self.db.get_message_or_user(
                            id=True,
                            message_id=message.reply_to_message.message_id,
                            bot_token=self.bot_token
                        )
                    )
            except Exception:
                pass


    async def admin_handler(self, message: Message):
        tg_id = message.from_user.id
        chat_id = message.chat.id

        admin_status = await self.is_admin(tg_id=tg_id)
        if admin_status:
            await self.dp.bot.send_message(
                chat_id=chat_id,
                text="Админ-панель",
                reply_markup=admin_markup
            )

    async def callback_admin_handler(self, call: CallbackQuery, state: FSMContext):
        chat = call["message"]["chat"]["id"]
        callback = call["data"]
        m_id = call.message.message_id

        if callback == "back-to-admin":
            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=m_id
            )

            await self.dp.bot.send_message(
                chat_id=chat,
                text="Админ-панель",
                reply_markup=admin_markup
            )
            await state.finish()

        elif callback == "message-to-users":
            await BotStates.mailing.set()

            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=m_id
            )

            await self.dp.bot.send_message(
                chat_id=chat,
                text="Введите сообщение, которое будет отправлено пользователям",
                reply_markup=back_to_admin_markup
            )

        elif callback == "get-statistics":
            response = self.db.get_statistics(bot_token=self.bot_token)
            text = f"Всего пользователей: {response['all_users']}\n" \
                   f"Пользователей, заблокировавших бота: {response['blocked']}\n" \
                   f"Пользователей, не заблокировавших бота: {response['unblocked']}"

            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=m_id
            )

            await self.dp.bot.send_message(
                chat_id=chat,
                text=text,
                reply_markup=back_to_admin_markup
            )

        elif callback == "add-command":
            await BotStates.add_command.set()

            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=m_id
            )

            await self.dp.bot.send_message(
                chat_id=chat,
                text="Введите команду, которую хотите зарегистрировать.\n"
                     "Пример: gift",
                reply_markup=back_to_admin_markup
            )

        elif callback == "edit-text-command":
            await BotStates.choose_command.set()

            commands_list = self.db.get_commands_list(bot_token=self.bot_token)
            message_text = "Введите название команды, описание которой хотите изменить"

            if commands_list is not None:
                commands = "".join([f"{num + 1}) {command}\n" for num, command in enumerate(commands_list)])
                message_text = message_text + "\nДоступный список команд:\n" + commands

            elif commands_list is None:
                message_text = "Пока нет ни одной команды."

            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=m_id
            )

            await self.dp.bot.send_message(
                chat_id=chat,
                text=message_text,
                reply_markup=back_to_admin_markup
            )

        elif callback == "edit-start-message":
            await BotStates.edit_start_message.set()

            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=m_id
            )

            await self.dp.bot.send_message(
                chat_id=chat,
                text="Введите новое стартовое сообщение",
                reply_markup=back_to_admin_markup
            )

        elif callback == "delete-command":
            await BotStates.delete_command.set()

            commands_list = self.db.get_commands_list(bot_token=self.bot_token)
            message_text = "Введите название команды, которую хотите удалить."

            if commands_list is not None:
                commands = "".join([f"{num + 1}) {command}\n" for num, command in enumerate(commands_list)])
                message_text = message_text + "\nДоступный список команд:\n" + commands

            elif commands_list is None:
                message_text = "Пока нет ни одной команды."

            await self.dp.bot.delete_message(
                chat_id=chat,
                message_id=m_id
            )

            await self.dp.bot.send_message(
                chat_id=chat,
                text=message_text,
                reply_markup=back_to_admin_markup
            )

    async def mailing_state_handler(self, message: Message, state: FSMContext):
        users = self.db.get_users(bot_token=self.bot_token)
        chat_id = message.chat.id
        try:
            for user in users:
                await self.dp.bot.copy_message(
                    chat_id=user,
                    from_chat_id=chat_id,
                    message_id=message.message_id
                )

        except BotBlocked:
            self.db.update_user_info(tg_id=user, bot_blocked=1, bot_token=self.bot_token)

        except Exception:
            pass

        finally:
            await state.finish()


    async def add_command_state_handler(self, message: Message, state: FSMContext):
        chat = message.chat.id
        text = message.text

        async with state.proxy() as data:
            data["title"] = text

        await BotStates.add_description.set()
        await self.dp.bot.send_message(
            chat_id=chat,
            text="Введите автоответ для команды."
        )

    async def add_description_state_handler(self, message: Message, state: FSMContext):
        chat = message.chat.id
        text = message.html_text

        async with state.proxy() as data:
            title = data["title"]
            self.db.add_command_with_description(
                title=title,
                description=text,
                bot_token=self.bot_token
            )
            self.full_commands = self.db.get_commands_list(bot_token=self.bot_token)
            #print("desc", self.full_commands)
            self.dp.register_message_handler(callback=self.commands, commands=self.full_commands)

            message_text = f"Теперь при вызове команды {title}, будет выводиться текст:\n\n" \
                           f"{text}"
            await self.dp.bot.send_message(
                chat_id=chat,
                text=message_text,
                parse_mode="html"
            )

            await state.finish()

    async def choose_command_state_handler(self, message: Message, state: FSMContext):
        chat = message.chat.id
        text = message.html_text

        if text in self.full_commands:
            async with state.proxy() as data:
                data["title"] = text

            await BotStates.edit_text_command.set()
            self.full_commands = self.db.get_commands_list(bot_token=self.bot_token)
            #print(message.text, self.full_commands)

            await self.dp.bot.send_message(
                chat_id=chat,
                text=f"Выбрана команда: {text}."
                     f"Введите новый автоответ для команды."
            )

        else:
            await self.dp.bot.send_message(
                chat_id=chat,
                text="Нет такой команды"
            )

    async def edit_text_command_state_handler(self, message: Message, state: FSMContext):
        chat = message.chat.id
        text = message.html_text

        async with state.proxy() as data:
            title = data["title"]
            self.db.add_command_with_description(
                title=title,
                description=text,
                bot_token=self.bot_token
            )
            self.full_commands = self.db.get_commands_list(bot_token=self.bot_token)
            #print(message.text, self.full_commands)
            self.dp.register_message_handler(callback=self.commands, commands=self.full_commands)

            message_text = f"Теперь при вызове команды {title}, будет выводиться текст:\n\n" \
                           f"{text}"
            await self.dp.bot.send_message(
                chat_id=chat,
                text=message_text,
                parse_mode="html"
            )

            await state.finish()

    async def edit_start_message(self, message: Message, state: FSMContext):
        chat = message.chat.id
        text = message.html_text

        self.db.start_message(text=text, method="save", bot_token=self.bot_token)
        self.full_commands = self.db.get_commands_list(bot_token=self.bot_token)
        self.dp.register_message_handler(callback=self.commands, commands=self.full_commands)
        self.dp.register_message_handler(callback=self.start_handler, commands=["start"], state="*")

        await self.dp.bot.send_message(
            chat_id=chat,
            text="Стартовое сообщение успешно изменено"
        )
        await state.finish()

    async def delete_command_state_handler(self, message: Message, state: FSMContext):
        chat = message.chat.id
        text = message.text
        commands_list = self.db.get_commands_list(bot_token=self.bot_token)

        if text in commands_list:
            self.db.delete_command(command=text, bot_token=self.bot_token)
            self.full_commands = self.db.get_commands_list(bot_token=self.bot_token)
            # print(message.text, self.full_commands)
            self.dp.register_message_handler(callback=self.commands, commands=self.full_commands)

            await self.dp.bot.send_message(
                chat_id=chat,
                text=f"Команда {text} успешно удалена"
            )
            await state.finish()

        else:
            await self.dp.bot.send_message(
                chat_id=chat,
                text="Нет такой команды."
            )


    async def is_admin(self, tg_id: int) -> bool:
        admins = self.db.get_admin(bot_token=self.bot_token)

        if admins is None:
            return False

        elif tg_id in admins:
            return True

    def start_bot(self, event_loop):
        try:
            event_loop.create_task(self.dp.start_polling())
        except RuntimeError:
            pass

    def add_handlers(self):
        self.dp.register_message_handler(callback=self.commands, commands=self.full_commands)
        self.dp.register_callback_query_handler(callback=self.callback_admin_handler, state="*")

        self.dp.register_message_handler(callback=self.start_handler, commands=["start"], state="*")
        self.dp.register_message_handler(callback=self.admin_handler, commands=["admin"], state="*")
        self.dp.register_message_handler(callback=self.text_handler, content_types=ContentTypes.ANY)
        self.dp.register_message_handler(self.admin_message_handler, IsReplyFilter(True), content_types=ContentTypes.ANY)
        self.dp.register_message_handler(callback=self.mailing_state_handler, content_types=ContentTypes.ANY, state=BotStates.mailing)
        self.dp.register_message_handler(callback=self.add_command_state_handler, content_types=ContentTypes.TEXT, state=BotStates.add_command)
        self.dp.register_message_handler(callback=self.add_description_state_handler, content_types=ContentTypes.ANY, state=BotStates.add_description)
        self.dp.register_message_handler(callback=self.choose_command_state_handler, content_types=ContentTypes.TEXT, state=BotStates.choose_command)
        self.dp.register_message_handler(callback=self.edit_text_command_state_handler, content_types=ContentTypes.TEXT, state=BotStates.edit_text_command)
        self.dp.register_message_handler(callback=self.edit_start_message, state=BotStates.edit_start_message),
        self.dp.register_message_handler(callback=self.delete_command_state_handler, content_types=ContentTypes.TEXT, state=BotStates.delete_command)


    def run(self, event_loop):
        self.add_handlers()
        event_loop.run_until_complete(self.start_bot(event_loop))
