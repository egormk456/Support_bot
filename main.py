from config import token, chat_link
from class_bot import MyBot

bot = MyBot(token=token, database_name="comments.db", chat_link=chat_link)
bot.run()