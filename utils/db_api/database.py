from sqlite3 import connect
from typing import List
import os
from utils.usefull_functions.opened_file import open_files


class Database:
    def __init__(self, name):
        self.connection = connect(name)
        self.cursor = self.connection.cursor()

        self.funnel_connection = connect("funnels.db")

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
            bot_token TEXT,
            title TEXT,
            description TEXT,
            audio BLOB,
            photo BLOB,
            video BLOB,
            video_note BLOB,
            document BLOB,
            document_name TEXT,
            markup_text TEXT,
            application_text TEXT,
            application_button TEXT,
            application_name TEXT
            )"""
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS start_message(
            bot_token TEXT PRIMARY KEY,
            greeting TEXT,
            audio BLOB,
            photo BLOB,
            video BLOB,
            video_note BLOB,
            document BLOB,
            document_name TEXT,
            markup_text TEXT,
            application_name TEXT
            );
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS invites_links(
                bot_token TEXT,
                name TEXT,
                invite_link_number INTEGER,
                people_from_link INTEGER
            )
            """
        )
        self.connection.commit()

    def start_message(self, method: str, bot_token: str, text=None, audio_name=None,
                      photo_name=None, video_name=None, video_note_name=None, document_name=None,
                      markup_text="0", application_text=None, application_button=None, application_name=None):

        if method == "save":
            audio_reader, photo_reader, video_reader, video_note_reader, document_reader = open_files(
                audio_name, photo_name, video_name, video_note_name, document_name
            )

            if document_name is not None:
                document_name = document_name[15:-4]
            info = (bot_token, text, audio_reader, photo_reader, video_reader, video_note_reader, document_reader, document_name, markup_text, application_text, application_button, application_name)

            self.cursor.execute(
                f"""
                INSERT OR REPLACE INTO start_message
                (bot_token, greeting, audio, photo, video, video_note, document, document_name, markup_text, application_text, application_button, application_name)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                info
            )

            self.connection.commit()

        elif method == "get":
            mess = self.cursor.execute(
                f"""
                SELECT greeting, audio, photo, video, video_note, document, document_name, markup_text, application_text, application_button, application_name FROM start_message
                WHERE bot_token='{bot_token}'
                """
            ).fetchone()
            self.connection.commit()
            return mess

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

    def add_command_with_description(self, title: str, bot_token: str, description=None, audio_name=None, photo_name=None, video_note_name=None, video_name=None, document_name=None,
                                     markup_text="0", application_text=None, application_button=None, application_name=None):
        title = title.lower()
        commands_list = self.get_commands_list(bot_token=bot_token)


        audio_reader, photo_reader, video_reader, video_note_reader, document_reader = open_files(
            audio_name, photo_name, video_name, video_note_name, document_name
        )
        if document_name is not None:
            document_name = document_name[15:-4]
        info = (title, description, audio_reader, photo_reader, video_reader, video_note_reader, document_reader, document_name, markup_text, application_text, application_button, application_name)
        if title in commands_list:
            self.cursor.execute(
                f"""
                UPDATE commands
                SET title=?, 
                description=?,
                audio=?,
                photo=?,
                video=?,
                video_note=?,
                document=?,
                document_name=?,
                markup_text=?,
                application_text=?,
                application_button=?,
                application_name=?
                WHERE bot_token='{bot_token}'
                AND title='{title}'
                """,
                info
            )

        else:
            self.cursor.execute(
                f"""
                INSERT OR REPLACE INTO commands
                (title, description, bot_token, audio, photo, video, video_note, document, document_name, markup_text, application_text,
            application_button, application_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (title, description, bot_token, audio_reader, photo_reader, video_reader, video_note_reader, document_reader, document_name, markup_text, application_text, application_button, application_name)
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
        commands = self.cursor.execute(
                        f"""
                        SELECT title FROM commands
                        WHERE bot_token='{bot_token}'
                        """
                    ).fetchall()

        self.connection.commit()

        if commands is not None:
            commands = [title[0] for title in commands]
            return commands
        return None

    def get_commands_with_descriptions(self, bot_token: str):
        commands_dict = {
            response[0]: response[1:] for response in
            self.cursor.execute(
                f"""
                SELECT title, description, audio, photo, video, video_note, document, document_name, markup_text, application_text, application_button, application_name FROM commands
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

    def update_command_name(self, bot_token: str, prev_name: str, new_name: str) -> None:
        self.cursor.execute(
            f"""
            UPDATE commands
            SET title='{new_name}'
            WHERE bot_token='{bot_token}'
            AND title='{prev_name}'
            """
        )
        self.connection.commit()

    # Настройки бота
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
        return None

    def delete_bot(self, token: str):
        tables_list = ["users_posts", "bots_chats", "users_messages", "bots", "statistics", "commands", "start_message", "invites_links"]

        for name in tables_list:
            self.cursor.execute(
                f"""
                DELETE FROM {name}
                WHERE bot_token='{token}'
                """
            )

            self.connection.commit()


    # Пригласительные ссылки
    def create_invite_link(self, token: str, name: str):
        link_number = self.get_links_amount(token=token)
        self.cursor.execute(
            f"""
            INSERT INTO invites_links
            (bot_token, name, invite_link_number, people_from_link)
            VALUES
            ('{token}', '{name}', {link_number + 1}, 0);
            """
        )

        self.connection.commit()
        return link_number + 1

    def get_links_amount(self, token):
        links = self.cursor.execute(
            f"""
            SELECT invite_link_number FROM invites_links
            WHERE bot_token='{token}'
            """
        ).fetchall()

        self.connection.commit()

        if links is None:
            return 0
        return len(links)

    def get_links_info(self, token: str):
        links_info = self.cursor.execute(
            f"""
            SELECT name, invite_link_number, people_from_link FROM invites_links
            WHERE bot_token='{token}'
            """
        ).fetchall()

        if links_info is None:
            return None

        #links_info = #[? for name, num, people in links_info]
        return sorted(links_info, key=lambda x: x[1])

    def get_link_info(self, token: str, link_num: int):
        link_info = self.cursor.execute(
            f"""
            SELECT name, people_from_link FROM invites_links
            WHERE bot_token='{token}'
            AND invite_link_number={link_num}
            """
        ).fetchone()

        if link_info is None:
            return None
        return link_info

    def update_link_views(self, token: str, link_num: int):
        name, people_amount = self.get_link_info(token=token, link_num=link_num)

        self.cursor.execute(
            f"""
            UPDATE invites_links
            SET people_from_link={people_amount + 1}
            WHERE bot_token='{token}'
            AND invite_link_number={link_num}
            """
        )

        self.connection.commit()

    def delete_invite_link(self, token: str, link_num: int):
        self.cursor.execute(
            f"""
            DELETE FROM invites_links
            WHERE bot_token='{token}'
            AND invite_link_number={link_num}
            """
        )

        self.connection.commit()

    def get_applications_names_list(self, token: str):
        lst_commands = self.cursor.execute(
                    f"""
                    SELECT application_name FROM commands
                    WHERE bot_token='{token}'
                    """
               ).fetchall()


        lst_steps = self.funnel_connection.cursor().execute(
                    f"""
                    SELECT application_name FROM steps
                    WHERE token='{token}'
                    """
               ).fetchall()


        lst_start = self.cursor.execute(
                    f"""
                    SELECT application_name FROM start_message
                    WHERE bot_token='{token}'
                    """
               ).fetchall()

        lst_commands.extend(lst_steps)
        lst_commands.extend(lst_start)

        lst_commands = [elem[0] for elem in lst_commands if elem[0] is not None]

        return lst_commands

    def get_application_text(self, application_name, token):
        lst_commands = self.cursor.execute(
                    f"""
                    SELECT application_text FROM commands
                    WHERE bot_token='{token}'
                    AND application_name='{application_name}'
                    """
               ).fetchall()


        lst_steps = self.funnel_connection.cursor().execute(
                    f"""
                    SELECT application_text FROM steps
                    WHERE token='{token}'
                    AND application_name='{application_name}'
                    """
               ).fetchall()


        lst_start = self.cursor.execute(
                    f"""
                    SELECT application_text FROM start_message
                    WHERE bot_token='{token}'
                    AND application_name='{application_name}'
                    """
               ).fetchall()

        lst_commands.extend(lst_steps)
        lst_commands.extend(lst_start)

        lst_commands = [elem[0] for elem in lst_commands if elem[0] is not None]
        return lst_commands[0]

    def transfer_bot(self, tg_id, token):
        self.cursor.execute(
            f"""
            UPDATE bots
            SET tg_id={tg_id}
            WHERE bot_token='{token}'
            """
        )

        self.connection.commit()

