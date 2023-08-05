from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


bots_markup = InlineKeyboardMarkup()
bots_markup.add(InlineKeyboardButton(text="🤖 Добавить бота", callback_data="add-bot"), InlineKeyboardButton(text="🐎 Мои боты", callback_data="my-bots"))
# bots_markup.add(InlineKeyboardButton(text="Настройка автоворонок", callback_data="funnel-settings"))
bots_markup.add(InlineKeyboardButton(text="👌🏻Помощь", callback_data="help"))


funnel_markup = InlineKeyboardMarkup()
funnel_markup.add(InlineKeyboardButton(text="Список автоворонок", callback_data="funnel-list"))
funnel_markup.add(InlineKeyboardButton(text="Добавить автоворонку", callback_data="add-funnel"))
funnel_markup.add(InlineKeyboardButton(text="Назад", callback_data="back-to-menu"))

autoanswers_markup = InlineKeyboardMarkup()
autoanswers_markup.add(InlineKeyboardButton(text="Добавить команду", callback_data="add-command"))
autoanswers_markup.add(InlineKeyboardButton(text="Изменить автоответ команды", callback_data="edit-text-command"))
autoanswers_markup.add(InlineKeyboardButton(text="Изменить команду", callback_data="edit-command"))
autoanswers_markup.add(InlineKeyboardButton(text="Удалить команду", callback_data="delete-command"))
autoanswers_markup.add(InlineKeyboardButton(text="Вернуться к настройкам бота", callback_data="back-to-admin"))

funnel_steps_markup = InlineKeyboardMarkup()
funnel_steps_markup.add(InlineKeyboardButton(text="Добавить триггер", callback_data="add-trigger"))
funnel_steps_markup.add(InlineKeyboardButton(text="Добавить шаг", callback_data="add-step"))
funnel_steps_markup.add(InlineKeyboardButton(text="Список шагов", callback_data="steps-list"))
funnel_steps_markup.add(InlineKeyboardButton(text="Удалить шаг", callback_data="delete-step"))
funnel_steps_markup.add(InlineKeyboardButton(text="Назад", callback_data="back-to-admin"))


invites = InlineKeyboardMarkup()
invites.add(InlineKeyboardButton(text="Мои пригласительные ссылки", callback_data="get_invites_links"))
invites.add(InlineKeyboardButton(text="Добавить пригласительную ссылку", callback_data="add_invite_link"))
invites.add(InlineKeyboardButton(text="Назад", callback_data="back-to-admin"))