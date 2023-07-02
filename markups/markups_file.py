from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


bots_markup = InlineKeyboardMarkup()
bots_markup.add(InlineKeyboardButton(text="Добавить бота", callback_data="add-bot"), InlineKeyboardButton(text="Мои боты", callback_data="my-bots"))
bots_markup.add(InlineKeyboardButton(text="Настройка автоворонок", callback_data="funnel-settings"))
bots_markup.add(InlineKeyboardButton(text="Помощь", callback_data="help"))


funnel_markup = InlineKeyboardMarkup()
funnel_markup.add(InlineKeyboardButton(text="Список автоворонок", callback_data="funnel-list"))
funnel_markup.add(InlineKeyboardButton(text="Добавить автоворонку", callback_data="add-funnel"))
funnel_markup.add(InlineKeyboardButton(text="Назад", callback_data="back-to-menu"))


funnel_steps_markup = InlineKeyboardMarkup()
funnel_steps_markup.add(InlineKeyboardButton(text="Добавить триггер", callback_data="add-trigger"))
funnel_steps_markup.add(InlineKeyboardButton(text="Добавить шаг", callback_data="add-step"))
funnel_steps_markup.add(InlineKeyboardButton(text="Список шагов", callback_data="steps-list"))
funnel_steps_markup.add(InlineKeyboardButton(text="Удалить шаг", callback_data="delete-step"))
funnel_steps_markup.add(InlineKeyboardButton(text="Назад", callback_data="back-to-fs"))
