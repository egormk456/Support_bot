from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

bots_markup = InlineKeyboardMarkup()

bots_markup.add(InlineKeyboardButton(text="Добавить бота", callback_data="add-bot"), InlineKeyboardButton(text="Мои боты", callback_data="my-bots"))
bots_markup.add(InlineKeyboardButton(text="Помощь", callback_data="help"))