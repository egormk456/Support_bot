from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_markup = InlineKeyboardMarkup()

admin_markup.add(InlineKeyboardButton(text="Рассылка пользователям", callback_data="message-to-users"))
admin_markup.add(InlineKeyboardButton(text="Посмотреть статистику", callback_data="get-statistics"))
admin_markup.add(InlineKeyboardButton(text="Добавить команду", callback_data="add-command"))
admin_markup.add(InlineKeyboardButton(text="Изменить автоответ команды", callback_data="edit-text-command"))
admin_markup.add(InlineKeyboardButton(text="Изменить стартовое сообщение", callback_data="edit-start-message"))
admin_markup.add(InlineKeyboardButton(text="Удалить команду", callback_data="delete-command"))