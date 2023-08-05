from sqlite3 import connect
from utils.db_api.database import Database
from utils.db_api.funnel_db import FunnelDatabase


class AdminDatabase:
    def __init__(self, db_name, funnel_db_name):
        self.connection = connect("admin.db")
        self.db = Database(db_name)
        self.funnel_db = FunnelDatabase(funnel_db_name)
        self.cursor = self.connection.cursor()

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
                tg_id INTEGER PRIMARY KEY
            )
            """
        )
        self.connection.commit()

    def get_all_users(self):
        tokens = self.db.get_tokens()

        tokens_and_users = {token: self.db.get_users(bot_token=token) for token in tokens}
        users_count = sum([len(users) for token, users in tokens_and_users.items()])
        return tokens_and_users, users_count

    def add_user(self, tg_id):
        self.cursor.execute(
            f"""
            INSERT OR REPLACE INTO users
            (tg_id)
            VALUES
            ({tg_id});
            """
        )
        self.connection.commit()

    def get_users(self):
        users = self.cursor.execute(
            """
            SELECT tg_id FROM users
            """
        ).fetchall()

        if users is not None and len(users) > 0:
            users = [user[0] for user in users]
            return users

        return None

    def get_statistics(self):
        users = self.get_users()
        print(users)
        if users is None:
            return None

        statistics_dict = dict()

        for user in users:
            tokens = self.db.get_tokens(tg_id=user)
            funnel_tokens = self.funnel_db.get_tokens(tg_id=user)
            users_count = 0

            if tokens is None:
                tokens = []

            else:
                for token in tokens:
                    users_count += len(self.db.get_users(bot_token=token))

            statistics_dict[user] = {
                "tokens": tokens,
                "funnel_count": len(funnel_tokens),
                "users_count": users_count
            }

        return statistics_dict