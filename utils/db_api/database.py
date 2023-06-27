from sqlite3 import connect
from typing import List


class Database:
    def __init__(self, name):
        self.connection = connect(name)
        self.cursor = self.connection.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users_posts(
            tg_id INTEGER PRIMARY KEY,
            bot_token TEXT,
            post_id INTEGER
        )"""
                            )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bots_chats(
            bot_token TEXT PRIMARY KEY,
            channel_id INTEGER,
            group_id INTEGER
            )
            """
        )

        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users_messages(
                tg_id INTEGER PRIMARY KEY,
                bot_token TEXT,
                message_id INTEGER
                )"""
                            )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bots(
            tg_id INTEGER,
            bot_token TEXT
            )"""
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS statistics(
            tg_id INTEGER PRIMARY KEY,
            bot_token TEXT,
            bot_blocked INTEGER
            )"""
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS commands(
            title TEXT PRIMARY KEY,
            description TEXT,
            bot_token TEXT
            )"""
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS start_message(
            bot_token TEXT PRIMARY KEY,
            greeting TEXT
            );
            """
        )
        self.connection.commit()

    def start_message(self, method: str, bot_token: str, text=None):
        if method == "save":
            self.cursor.execute(
                f"""
                INSERT OR REPLACE INTO start_message
                (bot_token, greeting)
                VALUES('{bot_token}', '{text}');
                """
            )
            self.connection.commit()

        elif method == "get":
            mess = self.cursor.execute(
                f"""
                SELECT greeting FROM start_message
                WHERE bot_token='{bot_token}'
                """
            ).fetchone()
            self.connection.commit()
            return mess[0]

    def update_user_info(self, tg_id: int, bot_token: str, bot_blocked: int) -> None:
        self.cursor.execute(
            f"""
            INSERT OR REPLACE INTO statistics
            (tg_id, bot_token, bot_blocked)
            VALUES
            ({tg_id}, '{bot_token}', {bot_blocked});
            """
        )
        self.connection.commit()

    def add_user_post(self, tg_id: int, bot_token: str, post_id: int) -> None:
        self.cursor.execute(
            f"""
            INSERT OR REPLACE INTO users_posts
            VALUES({tg_id}, '{bot_token}', {post_id})
            """
        )
        self.connection.commit()
        self.update_user_info(tg_id=tg_id, bot_token=bot_token, bot_blocked=0)

    def add_user_message(self, tg_id: int, bot_token: str, message_id: int) -> None:
        self.cursor.execute(
            f"""
            INSERT OR REPLACE INTO users_messages
            VALUES({tg_id}, '{bot_token}', {message_id})
            """
        )
        self.connection.commit()

    def add_command_with_description(self, title: str, description: str, bot_token: str):
        title = title.lower()

        self.cursor.execute(
            f"""
            INSERT OR REPLACE INTO commands
            (title, description, bot_token)
            VALUES ('{title}', '{description}', '{bot_token}');
            """
        )
        self.connection.commit()

    def add_bot(self, tg_id: int, bot_token: str) -> None:
        self.cursor.execute(
            f"""
            INSERT OR REPLACE INTO bots
            VALUES({tg_id}, '{bot_token}')
            """
        )
        self.connection.commit()

    def get_admin(self, bot_token: str) -> List[int] or None:
        admins = self.cursor.execute(
            f"""
            SELECT tg_id FROM bots
            WHERE bot_token='{bot_token}'
            """
        ).fetchall()

        if admins is not None:
            admins = [admin[0] for admin in admins]

        return admins

    def get_users(self, bot_token: str) -> List:
        data = self.cursor.execute(
            f"""
            SELECT tg_id FROM users_posts
            WHERE bot_token='{bot_token}'
            """
        ).fetchall()
        self.connection.commit()

        data = [item[0] for item in data]
        return data

    def get_message_or_user(self, bot_token: str, tg_id=None, message_id=None, id=None, message=None) -> int:
        if message:
            message_id_data = self.cursor.execute(
                f"""
                SELECT message_id FROM users_messages
                WHERE tg_id={tg_id} AND bot_token='{bot_token}'
                """
            ).fetchone()
            self.connection.commit()

            if message_id_data is not None:
                return message_id_data[0]

        elif id:
            tg_id_data = self.cursor.execute(
                f"""
                SELECT tg_id FROM users_messages
                WHERE message_id={message_id} AND bot_token='{bot_token}'
                """
            ).fetchone()
            self.connection.commit()

            if tg_id_data is not None:
                return tg_id_data[0]

    def get_post_id(self, tg_id: int, bot_token: str) -> int:
        post_id = self.cursor.execute(
            f"""
            SELECT post_id FROM users_posts
            WHERE tg_id={tg_id} AND bot_token='{bot_token}'
            """
        ).fetchone()
        self.connection.commit()

        if post_id is not None:
            return post_id[0]

    def get_statistics(self, bot_token: str):
        blocked = int()
        unblocked = int()

        data = self.cursor.execute(
            f"""
            SELECT bot_blocked FROM statistics
            WHERE bot_token='{bot_token}'
            """
        ).fetchall()

        for boolean in data:
            if boolean[0] == 1:
                blocked += 1

            elif boolean[0] == 0:
                unblocked += 1

        self.connection.commit()

        return dict(
            blocked=blocked,
            unblocked=unblocked,
            all_users=len(data)
        )

    def get_commands_list(self, bot_token: str):
        commands = [title[0] for title in
                    self.cursor.execute(
                        f"""
                        SELECT title FROM commands
                        WHERE bot_token='{bot_token}'
                        """
                    ).fetchall()
                    ]

        self.connection.commit()
        return commands

    def get_commands_with_descriptions(self, bot_token: str):
        commands_dict = {
            response[0]: response[1] for response in
            self.cursor.execute(
                f"""
                SELECT title, description FROM commands
                WHERE bot_token='{bot_token}'
                """
            ).fetchall()
        }

        self.connection.commit()
        return commands_dict

    def delete_command(self, command: str, bot_token: str) -> None:
        self.cursor.execute(
            f"""
            DELETE FROM commands
            WHERE title='{command}' AND bot_token='{bot_token}'
            """
        )
        self.connection.commit()

    def get_chat_link(self, bot_token: str):
        chat_link = self.cursor.execute(
            f"""
            SELECT channel_id FROM bots_chats
            WHERE bot_token='{bot_token}'
            """
        ).fetchone()
        self.connection.commit()

        if chat_link is None:
            return None

        return chat_link[0]

    def get_group_id(self, bot_token: str):
        group_id = self.cursor.execute(
            f"""
            SELECT group_id FROM bots_chats
            WHERE bot_token='{bot_token}'
            """
        ).fetchone()
        self.connection.commit()

        if group_id is None:
            return None
        return group_id[0]

    def set_group_to_bot(self, bot_token: str, channel_id: int, group_id: int) -> None:
        self.cursor.execute(
            f"""
            INSERT OR REPLACE INTO bots_chats
            (bot_token, channel_id, group_id)
            VALUES
            ('{bot_token}', {channel_id}, {group_id});
            """
        )
        self.connection.commit()

    def get_tokens(self, tg_id=None):
        if tg_id:
            tokens = self.cursor.execute(
                f"""
                SELECT bot_token FROM bots
                WHERE tg_id={tg_id}
                """
            ).fetchall()

            self.connection.commit()

        else:
            tokens = self.cursor.execute(
                """
                SELECT bot_token FROM bots
                """
            ).fetchall()

            self.connection.commit()

        if tokens is not None and len(tokens) > 0:
            tokens = [token[0] for token in tokens]
            return tokens