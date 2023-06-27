from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

back_to_menu_markup = InlineKeyboardMarkup()

back_to_menu_markup.add(InlineKeyboardButton(text="Назад", callback_data="back-to-menu"))