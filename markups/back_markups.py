from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

back_to_admin_markup = InlineKeyboardMarkup()
back_to_admin_markup.add(InlineKeyboardMarkup(text="Назад", callback_data="back-to-admin"))


back_to_menu_markup = InlineKeyboardMarkup()
back_to_menu_markup.add(InlineKeyboardButton(text="Назад", callback_data="back-to-menu"))


back_to_funnel_settings = InlineKeyboardMarkup()
back_to_funnel_settings.add(InlineKeyboardButton(text="Назад", callback_data="back-to-fs"))


back_to_funnel_steps = InlineKeyboardMarkup()
back_to_funnel_steps.add(InlineKeyboardButton(text="Назад", callback_data="back-to-funnel-steps"))