from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

back_to_admin_markup = InlineKeyboardMarkup()

back_to_admin_markup.add(InlineKeyboardMarkup(text="Назад", callback_data="back-to-admin"))