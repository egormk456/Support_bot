from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_markup = InlineKeyboardMarkup()

admin_markup.add(InlineKeyboardButton(text="Рассылка пользователям", callback_data="message-to-users"))
admin_markup.add(InlineKeyboardButton(text="Посмотреть статистику", callback_data="get-statistics"))
admin_markup.add(InlineKeyboardButton(text="Добавить команду", callback_data="add-command"))
admin_markup.add(InlineKeyboardButton(text="Изменить автоответ команды", callback_data="edit-text-command"))
admin_markup.add(InlineKeyboardButton(text="Изменить стартовое сообщение", callback_data="edit-start-message"))
admin_markup.add(InlineKeyboardButton(text="Удалить команду", callback_data="delete-command"))
admin_markup.add(InlineKeyboardButton(text="К списку ботов", callback_data="back-to-my-bots"))


admin_actions_markup = InlineKeyboardMarkup(row_width=1)

admin_actions_markup.add(InlineKeyboardButton(text="Получить статистику", callback_data="get-admin-statistics"))
admin_actions_markup.add(InlineKeyboardButton(text="Сделать рассылку по пользователям", callback_data="mailing"))
admin_actions_markup.add(InlineKeyboardButton(text="Сделать рассылку по дочерним ботам", callback_data="bots-mailing"))
admin_actions_markup.add(InlineKeyboardButton(text="Мои пригласительные ссылки", callback_data="AGIL"))
admin_actions_markup.add(InlineKeyboardButton(text="Добавить пригласительную ссылку", callback_data="AAIL"))