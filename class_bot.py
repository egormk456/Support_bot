from aiogram import Bot, Dispatcher
from aiogram.types import ContentTypes, Message, CallbackQuery
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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
from utils.usefull_functions.sending_message import sending_function
from utils.usefull_functions.create_markup import create_markup

loading_text = "🕒Загружаю..."


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


    async def start_handler(self, message: Message, call=None):
        users = self.db.get_users(bot_token=self.bot_token)
        tg_id = message.from_user.id
        chat = message.chat.id
        username = message.from_user.username
        text = message.text
        funnel_text = message.html_text


        if call is not None:
            username = message.chat.username
            tg_id = chat = message.chat.id
        #print(message)

        self.trigger = self.funnel_db.get_trigger(token=self.bot_token)
        self.funnel_users = self.funnel_db.get_users(token=self.bot_token)
        self.funnel_users = [user[0] for user in self.funnel_users]

        links_numbers = self.db.get_links_info(token=self.bot_token)
        links_numbers = [elem[1] for elem in links_numbers]

        if len(text[7:]) > 0 and int(text[7:]) in links_numbers:
            self.db.update_link_views(
                token=self.bot_token,
                link_num=int(text[7:])
            )

        if text[7:] == "1111111":
            await BotStates.mailing.set()

            await self.bot.send_message(
                chat_id=chat,
                text="Теперь вы можете отправлять любые объекты (текст, фото, стикеры - всё, что угодно).\n\n"
                     "/cancel чтобы выйти"
            )

        else:
            if self.trigger is not None and tg_id not in self.funnel_users and self.trigger.lower() == funnel_text.lower():
                self.funnel_db.add_or_update_user(token=self.bot_token, tg_id=tg_id, trigger_time=f"{datetime.now().hour * 60 + datetime.now().minute} {datetime.now().day}")

            greeting, audio, photo, video, video_note, document, document_name, markup_text, application_text, application_button, application_name = self.db.start_message(method="get", bot_token=self.bot_token)

            if application_button is None:
                application_button = "Оставить заявку"

            markup = InlineKeyboardMarkup()
            if application_name is not None:
                markup.add(
                    InlineKeyboardButton(
                        text=application_button, callback_data=application_name
                    )
                )

            loading_message = await self.bot.send_message(
                chat_id=chat,
                text=loading_text
            )

            commands_list = self.db.get_commands_list(bot_token=self.bot_token)
            if markup_text != "0":
                markup = create_markup(markup_text=markup_text, markup=markup, commands_list=commands_list)

            await sending_function(
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

            await self.bot.delete_message(
                chat_id=chat,
                message_id=loading_message.message_id
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

    async def cancel_handler(self, message: Message, state: FSMContext):
        user_state = await state.get_state()
        if user_state == "BotStates:mailing":
            await state.finish()

    async def text_handler(self, message: Message, state: FSMContext):
        tg_id = message.from_user.id
        m_id = message.message_id
        text = message.html_text
        chat_type = message.chat.type
        funnel_text = message.text
        #print(message)
        self.full_commands = self.db.get_commands_list(bot_token=self.bot_token)
        self.trigger = self.funnel_db.get_trigger(token=self.bot_token)
        self.funnel_users = self.funnel_db.get_users(token=self.bot_token)
        self.funnel_users = [user[0] for user in self.funnel_users]
        #print(self.full_commands, text)

        if text == "/start":
            await self.start_handler(message)

        if self.trigger is not None and tg_id not in self.funnel_users and self.trigger.lower() == funnel_text.lower():
            self.funnel_db.add_or_update_user(token=self.bot_token, tg_id=tg_id,
                                              trigger_time=f"{datetime.now().hour * 60 + datetime.now().minute} {datetime.now().day}")

        if message.chat.id == self.group_id and text != "/set_group":
            await self.admin_message_handler(message=message)

        elif text is not None and text in self.full_commands:
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

    async def edited_messages(self, message: Message, state: FSMContext):
        chat_type = message.chat.type
        tg_id = message.from_user.id
        m_id = message.message_id

        if chat_type == "private":
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

    async def commands(self, message: Message, state: FSMContext, call=None):
        chat = message.chat.id
        m_id = message.message_id
        funnel_text = message.text

        if call is not None:
            username = message.chat.username
            tg_id = chat = message.chat.id

        if message.chat.type == "private":
            loading_message = await self.bot.send_message(
                chat_id=chat,
                text=loading_text
            )

            self.trigger = self.funnel_db.get_trigger(token=self.bot_token)
            self.funnel_users = self.funnel_db.get_users(token=self.bot_token)
            self.funnel_users = [user[0] for user in self.funnel_users]
            print(chat, self.funnel_users, self.trigger, funnel_text)
            if self.trigger is not None and chat not in self.funnel_users and self.trigger.lower() == funnel_text.lower():
                self.funnel_db.add_or_update_user(token=self.bot_token, tg_id=chat,
                                                  trigger_time=f"{datetime.now().hour * 60 + datetime.now().minute} {datetime.now().day}")

            if call is None:
                message_to_chat = await self.dp.bot.copy_message(
                    chat_id=self.group_id,
                    from_chat_id=chat,
                    message_id=m_id,
                    reply_to_message_id=self.db.get_post_id(tg_id=chat, bot_token=self.bot_token)
                )

                self.db.add_user_message(tg_id=chat, message_id=message_to_chat.message_id, bot_token=self.bot_token)
            commands_dict = self.db.get_commands_with_descriptions(bot_token=self.bot_token)
            description, audio, photo, video, video_note, document, document_name, markup_text, application_text, application_button, application_name = commands_dict[message.text]

            if application_button is None:
                application_button = "Оставить заявку"

            markup = InlineKeyboardMarkup()
            if application_name is not None:
                markup.add(
                    InlineKeyboardButton(
                        text=application_button, callback_data=application_name
                    )
                )

            commands_list = self.db.get_commands_list(bot_token=self.bot_token)
            if markup_text != "0":
                markup = create_markup(markup_text=markup_text, markup=markup, commands_list=commands_list)

            await sending_function(
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

            await self.bot.delete_message(
                chat_id=chat,
                message_id=loading_message.message_id
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


    async def callback_admin_handler(self, call: CallbackQuery, state: FSMContext):
        chat = call["message"]["chat"]["id"]
        callback = call["data"]
        m_id = call.message.message_id
        username = call["from"]["username"]
        applications_names_list = self.db.get_applications_names_list(token=self.bot_token)

        commands_list = self.db.get_commands_list(bot_token=self.bot_token)
        commands_dict = self.db.get_commands_with_descriptions(bot_token=self.bot_token)
        print(call)
        if not call.message.chat.type == "private":
            return

        if callback != "/start" and callback not in applications_names_list:
            description, audio, photo, video, video_note, document, document_name, markup_text, application_text, application_button, application_name = commands_dict[callback]

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

        elif callback == "/start":
            call.message["text"] = callback
            await self.start_handler(call.message, call=True)

        elif callback in commands_list:
            # await self.dp.bot.delete_message(
            #     chat_id=chat,
            #     message_id=m_id
            # )
            call.message.text = callback
            await self.commands(call.message, state, call=True)

        elif callback in applications_names_list:
            # await self.dp.bot.delete_message(
            #     chat_id=chat,
            #     message_id=m_id
            # )

            message_to_chat = await self.bot.send_message(
                chat_id=self.group_id,
                text=f"Новая заявка по теме: <b>{callback}</b>\n"
                     f"От: @{username}",
                parse_mode="html",
                reply_to_message_id=self.db.get_post_id(tg_id=chat, bot_token=self.bot_token)
            )
            self.db.add_user_message(tg_id=chat, message_id=message_to_chat.message_id, bot_token=self.bot_token)

            application_text = self.db.get_application_text(application_name=callback, token=self.bot_token)
            await self.bot.send_message(
                chat_id=chat,
                text=application_text,
                parse_mode="html"
            )

    async def mailing_state_handler(self, message: Message, state: FSMContext):
        users = self.db.get_users(bot_token=self.bot_token)
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

                        except BotBlocked:
                            self.db.update_user_info(tg_id=user, bot_blocked=1, bot_token=self.bot_token)
                            continue

                        except Exception as e:
                            print(e)
                            continue

                        finally:
                            await state.finish()

                    response = self.db.get_statistics(bot_token=self.bot_token)


                    await self.dp.bot.send_message(
                        chat_id=chat_id,
                        text=f"<b>Найдено пользователей:</b> {response['all_users']}\n\n"
                             f"Отправлено: {response['unblocked']} из {response['all_users']}\n"
                             f"Заблокировали бота: {response['blocked']}",
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

    # async def add_command_state_handler(self, message: Message, state: FSMContext):
    #     chat = message.chat.id
    #     text = message.text
    #
    #     async with state.proxy() as data:
    #         data["title"] = text
    #
    #     await BotStates.add_description.set()
    #     await self.dp.bot.send_message(
    #         chat_id=chat,
    #         text="Введите автоответ для команды."
    #     )

    # async def add_description_state_handler(self, message: Message, state: FSMContext):
    #     chat = message.chat.id
    #     text = message.html_text
    #
    #     async with state.proxy() as data:
    #         title = data["title"]
    #         self.db.add_command_with_description(
    #             title=title,
    #             description=text,
    #             bot_token=self.bot_token
    #         )
    #         self.full_commands = self.db.get_commands_list(bot_token=self.bot_token)
    #         #print("desc", self.full_commands)
    #         self.dp.register_message_handler(callback=self.commands, commands=self.full_commands)
    #
    #         message_text = f"Теперь при вызове команды {title}, будет выводиться текст:\n\n" \
    #                        f"{text}"
    #         await self.dp.bot.send_message(
    #             chat_id=chat,
    #             text=message_text,
    #             parse_mode="html"
    #         )
    #
    #         await state.finish()
    #
    # async def choose_command_state_handler(self, message: Message, state: FSMContext):
    #     chat = message.chat.id
    #     text = message.html_text
    #
    #     if text in self.full_commands:
    #         async with state.proxy() as data:
    #             data["title"] = text
    #
    #         await BotStates.edit_text_command.set()
    #         self.full_commands = self.db.get_commands_list(bot_token=self.bot_token)
    #         #print(message.text, self.full_commands)
    #
    #         await self.dp.bot.send_message(
    #             chat_id=chat,
    #             text=f"Выбрана команда: {text}."
    #                  f"Введите новый автоответ для команды."
    #         )
    #
    #     else:
    #         await self.dp.bot.send_message(
    #             chat_id=chat,
    #             text="Нет такой команды"
    #         )
    #
    # async def edit_text_command_state_handler(self, message: Message, state: FSMContext):
    #     chat = message.chat.id
    #     text = message.html_text
    #
    #     async with state.proxy() as data:
    #         title = data["title"]
    #         self.db.add_command_with_description(
    #             title=title,
    #             description=text,
    #             bot_token=self.bot_token
    #         )
    #         self.full_commands = self.db.get_commands_list(bot_token=self.bot_token)
    #         #print(message.text, self.full_commands)
    #         self.dp.register_message_handler(callback=self.commands, commands=self.full_commands)
    #
    #         message_text = f"Теперь при вызове команды {title}, будет выводиться текст:\n\n" \
    #                        f"{text}"
    #         await self.dp.bot.send_message(
    #             chat_id=chat,
    #             text=message_text,
    #             parse_mode="html"
    #         )
    #
    #         await state.finish()
    #
    # async def edit_start_message(self, message: Message, state: FSMContext):
    #     chat = message.chat.id
    #     text = message.html_text
    #
    #     self.db.start_message(text=text, method="save", bot_token=self.bot_token)
    #     self.full_commands = self.db.get_commands_list(bot_token=self.bot_token)
    #     self.dp.register_message_handler(callback=self.commands, commands=self.full_commands)
    #     self.dp.register_message_handler(callback=self.start_handler, commands=["start"], state="*")
    #
    #     await self.dp.bot.send_message(
    #         chat_id=chat,
    #         text="Стартовое сообщение успешно изменено"
    #     )
    #     await state.finish()
    #
    # async def delete_command_state_handler(self, message: Message, state: FSMContext):
    #     chat = message.chat.id
    #     text = message.text
    #     commands_list = self.db.get_commands_list(bot_token=self.bot_token)
    #
    #     if text in commands_list:
    #         self.db.delete_command(command=text, bot_token=self.bot_token)
    #         self.full_commands = self.db.get_commands_list(bot_token=self.bot_token)
    #         # print(message.text, self.full_commands)
    #         self.dp.register_message_handler(callback=self.commands, commands=self.full_commands)
    #
    #         await self.dp.bot.send_message(
    #             chat_id=chat,
    #             text=f"Команда {text} успешно удалена"
    #         )
    #         await state.finish()
    #
    #     else:
    #         await self.dp.bot.send_message(
    #             chat_id=chat,
    #             text="Нет такой команды."
    #         )


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
        # self.dp.register_message_handler(callback=self.commands, commands=self.full_commands)
        self.dp.register_callback_query_handler(callback=self.callback_admin_handler, state="*")

        self.dp.register_message_handler(callback=self.start_handler, commands=["start"], state="*")
        self.dp.register_message_handler(callback=self.text_handler, content_types=ContentTypes.ANY)
        self.dp.register_edited_message_handler(callback=self.edited_messages, content_types=ContentTypes.ANY)
        self.dp.register_message_handler(self.admin_message_handler, IsReplyFilter(True), content_types=ContentTypes.ANY)
        self.dp.register_message_handler(callback=self.mailing_state_handler, content_types=ContentTypes.ANY, state=BotStates.mailing)
        # self.dp.register_message_handler(callback=self.add_command_state_handler, content_types=ContentTypes.TEXT, state=BotStates.add_command)
        # self.dp.register_message_handler(callback=self.add_description_state_handler, content_types=ContentTypes.ANY, state=BotStates.add_description)
        # self.dp.register_message_handler(callback=self.choose_command_state_handler, content_types=ContentTypes.TEXT, state=BotStates.choose_command)
        # self.dp.register_message_handler(callback=self.edit_text_command_state_handler, content_types=ContentTypes.TEXT, state=BotStates.edit_text_command)
        # self.dp.register_message_handler(callback=self.edit_start_message, state=BotStates.edit_start_message),
        # self.dp.register_message_handler(callback=self.delete_command_state_handler, content_types=ContentTypes.TEXT, state=BotStates.delete_command)


    def run(self, event_loop):
        self.add_handlers()
        event_loop.run_until_complete(self.start_bot(event_loop))
