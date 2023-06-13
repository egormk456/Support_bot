from aiogram import Bot, Dispatcher, executor
from aiogram.types import ContentTypes, Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import IsReplyFilter
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import BotBlocked

from utils.db_api.database import Database
from markups.admin_markup import admin_markup
from markups.back_to_admin_markup import back_to_admin_markup

from handlers.bot_states import BotStates
from aiogram.utils.exceptions import BadRequest



class MyBot:
    def __init__(self, token, database_name, chat_link):
        memory = MemoryStorage()
        self.bot = Bot(token=token)
        self.dp = Dispatcher(self.bot, storage=memory)
        self.db = Database(name=database_name)
        self.chat_link = chat_link
        self.full_commands = self.db.get_commands_list()


    async def start_handler(self, message):
        users = self.db.get_users()
        tg_id = message.from_user.id
        chat = message.chat.id
        username = message.from_user.username
        m_id = message.message_id
        text = message.text

        await self.dp.bot.send_message(
            chat_id=chat,
            text=self.db.start_message(method="get")
        )
        if tg_id not in users:
            try:
                message_to_chat = await self.dp.bot.send_message(
                    chat_id=self.chat_link, text=f"Чат с пользователем @{username}",
                )

                reply_message = await self.dp.bot.send_message(
                    chat_id=-1001806354820, #-1001807960416,
                    text="Новый чат",
                )
                self.db.add_user_post(tg_id=tg_id, post_id=reply_message.message_id + 1)

            except Exception as e:
                print(e)

    async def text_handler(self, message, state):
        tg_id = message.from_user.id
        username = message.from_user.username
        m_id = message.message_id
        text = message.text
        chat_type = message.chat.type

        if text[0] == "/" and text[1:] in self.full_commands:
            await self.commands(message=message, state=state)

        elif chat_type == "private":
            try:
                message_to_chat = await self.dp.bot.copy_message(
                    chat_id=-1001806354820, #-1001807960416,
                    from_chat_id=tg_id,
                    message_id=m_id,
                    reply_to_message_id=self.db.get_post_id(tg_id=tg_id)
                )
                self.db.add_user_message(tg_id=tg_id, message_id=message_to_chat.message_id)

            except BadRequest as e:
                pass

            except Exception as e:
                print(e)

    async def commands(self, message, state):
        chat = message.chat.id
        commands_dict = self.db.get_commands_with_descriptions()
        await self.dp.bot.send_message(
            chat_id=chat,
            text=commands_dict[message.text[1:]]
        )


    async def admin_message_handler(self, message):
        chat_type = message.chat.type
        print(message)
        if chat_type == "supergroup":
            if message.sender_chat is None or message.sender_chat.type != "channel":
                message_to_user = await self.dp.bot.copy_message(
                    from_chat_id=message.chat.id,
                    message_id=message.message_id,
                    chat_id=self.db.get_message_or_user(
                        id=True,
                        message_id=message.reply_to_message.message_id
                    )
                )


    async def admin_handler(self, message):
        tg_id = message.from_user.id
        chat_id = message.chat.id

        admin_status = await self.is_admin(tg_id=tg_id)
        if admin_status:
            await self.dp.bot.send_message(
                chat_id=chat_id,
                text="Админ-панель",
                reply_markup=admin_markup
            )

    async def callback_admin_handler(self, call, state):
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
            response = self.db.get_statistics()
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

            commands_list = self.db.get_commands_list()
            message_text = "Введите название команды, описание которой хотите изменить"

            if commands_list is not None:
                commands = "".join([f"{num + 1}) {command}\n" for num, command in enumerate(commands_list)])
                message_text = message_text + f"\nДоступный список команд:\n" + commands

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

            commands_list = self.db.get_commands_list()
            message_text = "Введите название команды, которую хотите удалить."

            if commands_list is not None:
                commands = "".join([f"{num + 1}) {command}\n" for num, command in enumerate(commands_list)])
                message_text = message_text + f"\nДоступный список команд:\n" + commands

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

    async def mailing_state_handler(self, message, state):
        users = self.db.get_users()
        chat_id = message.chat.id
        try:
            for user in users:
                await self.dp.bot.copy_message(
                    chat_id=user,
                    from_chat_id=chat_id,
                    message_id=message.message_id
                )

        except BotBlocked:
            self.db.update_user_info(tg_id=user, bot_blocked=1)

        except Exception as e:
            pass

        finally:
            await state.finish()


    async def add_command_state_handler(self, message, state):
        chat = message.chat.id
        text = message.text

        async with state.proxy() as data:
            data["title"] = text

        await BotStates.add_description.set()
        await self.dp.bot.send_message(
            chat_id=chat,
            text="Введите автоответ для команды."
        )

    async def add_description_state_handler(self, message, state):
        chat = message.chat.id
        text = message.text

        async with state.proxy() as data:
            title = data["title"]
            self.db.add_command_with_description(
                title=title,
                description=text
            )
            self.full_commands = self.db.get_commands_list()
            print("desc", self.full_commands)
            self.dp.register_message_handler(callback=self.commands, commands=self.full_commands)

            message_text = f"Теперь при вызове команды {title}, будет выводиться текст:\n\n" \
                           f"{text}"
            await self.dp.bot.send_message(
                chat_id=chat,
                text=message_text
            )

            await state.finish()

    async def choose_command_state_handler(self, message, state):
        chat = message.chat.id
        text = message.text

        if text in self.full_commands:
            async with state.proxy() as data:
                data["title"] = text

            await BotStates.edit_text_command.set()
            self.full_commands = self.db.get_commands_list()
            print(message.text, self.full_commands)

            await self.dp.bot.send_message(
                chat_id=chat,
                text=f"Выбрана команда: {text}."
                     f"Введите новый автоответ для команды."
            )

        else:
            await self.dp.bot.send_message(
                chat_id=chat,
                text=f"Нет такой команды"
            )

    async def edit_text_command_state_handler(self, message, state):
        chat = message.chat.id
        text = message.text

        async with state.proxy() as data:
            title = data["title"]
            self.db.add_command_with_description(
                title=title,
                description=text
            )
            self.full_commands = self.db.get_commands_list()
            print(message.text, self.full_commands)
            self.dp.register_message_handler(callback=self.commands, commands=self.full_commands)

            message_text = f"Теперь при вызове команды {title}, будет выводиться текст:\n\n" \
                           f"{text}"
            await self.dp.bot.send_message(
                chat_id=chat,
                text=message_text
            )

            await state.finish()

    async def edit_start_message(self, message, state):
        chat = message.chat.id
        text = message.text

        self.db.start_message(text=text, method="save")
        self.full_commands = self.db.get_commands_list()
        self.dp.register_message_handler(callback=self.commands, commands=self.full_commands)
        self.dp.register_message_handler(callback=self.start_handler, commands=["start"], state="*")

        await self.dp.bot.send_message(
            chat_id=chat,
            text="Стартовое сообщение успешно изменено"
        )
        await state.finish()

    async def delete_command_state_handler(self, message, state):
        chat = message.chat.id
        text = message.text
        commands_list = self.db.get_commands_list()

        if text in commands_list:
            self.db.delete_command(command=text)
            self.full_commands = self.db.get_commands_list()
            #print(message.text, self.full_commands)
            self.dp.register_message_handler(callback=self.commands, commands=self.full_commands)

            await self.dp.bot.send_message(
                chat_id=chat,
                text=f"Команда {text} успешно удалена"
            )
            await state.finish()

        else:
            await self.dp.bot.send_message(
                chat_id=chat,
                text=f"Нет такой команды."
            )


    async def is_admin(self, tg_id: int) -> bool:
        admins = self.db.get_admins()

        if admins is None:
            return False

        elif tg_id in admins:
            return True

    def add_handlers(self):
        self.dp.register_message_handler(callback=self.commands, commands=self.full_commands)
        self.dp.register_callback_query_handler(callback=self.callback_admin_handler, state="*")

        self.dp.register_message_handler(self.admin_message_handler, IsReplyFilter(True), content_types=ContentTypes.ANY)
        self.dp.register_message_handler(callback=self.admin_handler, commands=["admin"], state="*")
        self.dp.register_message_handler(callback=self.mailing_state_handler, content_types=ContentTypes.ANY, state=BotStates.mailing)
        self.dp.register_message_handler(callback=self.add_command_state_handler, content_types=ContentTypes.TEXT, state=BotStates.add_command)
        self.dp.register_message_handler(callback=self.add_description_state_handler, content_types=ContentTypes.ANY, state=BotStates.add_description)
        self.dp.register_message_handler(callback=self.choose_command_state_handler, content_types=ContentTypes.TEXT, state=BotStates.choose_command)
        self.dp.register_message_handler(callback=self.edit_text_command_state_handler, content_types=ContentTypes.TEXT, state=BotStates.edit_text_command)
        self.dp.register_message_handler(callback=self.edit_start_message, state=BotStates.edit_start_message),
        self.dp.register_message_handler(callback=self.delete_command_state_handler, content_types=ContentTypes.TEXT, state=BotStates.delete_command)
        self.dp.register_message_handler(callback=self.start_handler, commands=["start"], state="*")
        self.dp.register_message_handler(callback=self.text_handler, content_types=ContentTypes.TEXT)

    def run(self):
        self.add_handlers()
        executor.start_polling(dispatcher=self.dp, skip_updates=True)