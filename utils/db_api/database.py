from sqlite3 import connect
from typing import List, Dict


class Database:
    def __init__(self, name):
        self.connection = connect(name)
        self.cursor = self.connection.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_posts(
        tg_id INTEGER PRIMARY KEY,
        post_id INTEGER
        )"""
                            )

        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users_messages(
                tg_id INTEGER PRIMARY KEY,
                message_id INTEGER
                )"""
                            )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS admins(
            tg_id INTEGER PRIMARY KEY
            )"""
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS statistics(
            tg_id INTEGER PRIMARY KEY,
            bot_blocked INTEGER
            )"""
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS commands(
            title TEXT PRIMARY KEY,
            description TEXT
            )"""
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS start_message(
            id PRIMARY KEY,
            greeting TEXT
            );
            """
        )
        self.connection.commit()

    def start_message(self, method: str, text=None):
        if method == "save":
            self.cursor.execute(
                f"""
                INSERT OR REPLACE INTO start_message
                (id, greeting)
                VALUES(1, '{text}');
                """
            )

        elif method == "get":
            mess = self.cursor.execute(
                f"""
                SELECT greeting FROM start_message
                WHERE id=1
                """
            ).fetchone()

            return mess[0]

    def update_user_info(self, tg_id: int, bot_blocked: int) -> None:
        self.cursor.execute(
            f"""
            INSERT OR REPLACE INTO statistics
            (tg_id, bot_blocked)
            VALUES
            ({tg_id}, {bot_blocked});
            """
        )
        self.connection.commit()

    def add_user_post(self, tg_id: int, post_id: int) -> None:
        self.cursor.execute(
            f"""
            INSERT OR REPLACE INTO users_posts
            VALUES({tg_id}, {post_id})
            """
        )
        self.connection.commit()
        self.update_user_info(tg_id=tg_id, bot_blocked=0)

    def add_user_message(self, tg_id: int, message_id: int) -> None:
        self.cursor.execute(
            f"""
            INSERT OR REPLACE INTO users_messages
            VALUES({tg_id}, {message_id})
            """
        )
        self.connection.commit()

    def add_command_with_description(self, title: str, description: str):
        title = title.lower()

        self.cursor.execute(
            f"""
            INSERT OR REPLACE INTO commands
            (title, description)
            VALUES ('{title}', '{description}');
            """
        )
        self.connection.commit()

    def add_admin(self, tg_id: int) -> None:
        self.cursor.execute(
            f"""
            INSERT OR REPLACE INTO admins
            VALUES({tg_id})
            """
        )

    def get_admins(self) -> List[int] or None:
        admins = self.cursor.execute(
            """
            SELECT tg_id FROM admins
            """
        ).fetchall()

        if admins is not None:
            admins = [admin[0] for admin in admins]

        return admins

    def get_users(self) -> List:
        data = self.cursor.execute(
            """SELECT tg_id FROM users_posts"""
        ).fetchall()
        self.connection.commit()

        data = [item[0] for item in data]
        return data

    def get_message_or_user(self, tg_id=None, message_id=None, id=None, message=None) -> int:
        if message:
            message_id_data = self.cursor.execute(
                f"""
                SELECT message_id FROM users_messages
                WHERE tg_id={tg_id}
                """
            ).fetchone()
            self.connection.commit()

            if message_id_data is not None:
                return message_id_data[0]

        elif id:
            tg_id_data = self.cursor.execute(
                f"""
                SELECT tg_id FROM users_messages
                WHERE message_id={message_id}
                """
            ).fetchone()
            self.connection.commit()

            if tg_id_data is not None:
                return tg_id_data[0]

    def get_post_id(self, tg_id: int) -> int:
        post_id = self.cursor.execute(
            f"""
            SELECT post_id FROM users_posts
            WHERE tg_id={tg_id}
            """
        ).fetchone()
        self.connection.commit()

        if post_id is not None:
            return post_id[0]

    def get_statistics(self):
        blocked = int()
        unblocked = int()

        data = self.cursor.execute(
            """
            SELECT bot_blocked FROM statistics
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

    def get_commands_list(self):
        commands = [title[0] for title in
                    self.cursor.execute(
                        """
                        SELECT title FROM commands
                        """
                    ).fetchall()
                    ]

        self.connection.commit()
        return commands

    def get_commands_with_descriptions(self):
        commands_dict = {
            response[0]: response[1] for response in
            self.cursor.execute(
                """
                SELECT title, description FROM commands
                """
            ).fetchall()
        }

        self.connection.commit()
        return commands_dict

    def delete_command(self, command: str) -> None:
        self.cursor.execute(
            f"""
            DELETE FROM commands
            WHERE title='{command}'
            """
        )
        self.connection.commit()