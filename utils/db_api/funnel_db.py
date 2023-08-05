from sqlite3 import connect
from utils.usefull_functions.opened_file import open_files


class FunnelDatabase:
    def __init__(self, name):
        self.connection = connect(name)
        self.cursor = self.connection.cursor()

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS funnels(
                tg_id INTEGER,
                token TEXT
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users_steps(
            tg_id INTEGER,
            token TEXT,
            trigger_time TEXT,
            step_number INTEGER
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS triggers(
                tg_id INTEGER,
                token TEXT,
                trigger TEXT
            )
            """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS steps(
                tg_id INTEGER,
                token TEXT,
                step TEXT,
                minutes INTEGER,
                step_number INTEGER,
                audio BLOB,
                photo BLOB,
                video BLOB,
                video_note BLOB,
                document BLOB,
                markup_text TEXT, 
                application_name TEXT
            )
            """
        )

        self.connection.commit()

    def get_tokens(self, tg_id=None):
        if tg_id is None:
            tokens = self.cursor.execute(
                f"""
                SELECT token FROM funnels
                """
            ).fetchall()
        else:
            tokens = self.cursor.execute(
                f"""
                SELECT token FROM funnels
                WHERE tg_id={tg_id}
                """
            ).fetchall()
        self.connection.commit()

        if tokens is None:
            tokens = []

        else:
            tokens = [token[0] for token in tokens]

        return tokens

    def add_or_update_user(self, token: str, tg_id: int, trigger_time: str, step_number=None):

        if step_number is not None:
            self.cursor.execute(
                f"""
                UPDATE users_steps
                SET step_number={step_number}
                WHERE tg_id={tg_id}
                AND token='{token}'
                """
            )
            self.connection.commit()

        else:
            self.cursor.execute(
                f"""
                INSERT OR REPLACE INTO users_steps
                (tg_id, token, trigger_time, step_number)
                VALUES
                ({tg_id}, '{token}', '{trigger_time}', 1);
                """
            )
            self.connection.commit()

    def add_funnel(self, token: str, tg_id: int):
        self.cursor.execute(
            f"""
            INSERT INTO funnels
            (tg_id, token)
            VALUES
            ({tg_id}, '{token}');
            """
        )

        self.connection.commit()

    def get_trigger(self, token: str):
        trigger = self.cursor.execute(
            f"""
            SELECT trigger FROM triggers
            WHERE token='{token}'
            """
        ).fetchone()

        self.connection.commit()

        if trigger is None:
            return None
        return trigger[0]

    def add_trigger(self, token: str, tg_id: int, trigger: str):
        print(trigger, token)
        if self.get_trigger(token=token) is not None:
            self.cursor.execute(
                f"""
                UPDATE triggers
                SET trigger='{trigger}'
                WHERE token='{token}'
                """
            )

        else:
            self.cursor.execute(
                f"""
                INSERT OR REPLACE INTO triggers
                (tg_id, token, trigger)
                VALUES
                ({tg_id}, '{token}', '{trigger}');
                """
            )

        self.connection.commit()

    def add_step(self, tg_id: int, token: str, step: str, minutes: int, audio_name=None, photo_name=None, video_note_name=None, video_name=None, document_name=None,
                 markup_text="0", application_name=None):
        step_number = self.get_steps_length(token=token)

        audio_reader, photo_reader, video_reader, video_note_reader, document_reader = open_files(
            audio_name, photo_name, video_name, video_note_name, document_name
        )

        info = (tg_id, token, step, minutes, step_number + 1, audio_reader, photo_reader, video_reader, video_note_reader, document_reader, markup_text, application_name)
        #print(info)
        self.cursor.execute(
            f"""
            INSERT OR REPLACE INTO steps
            (tg_id, token, step, minutes, step_number, audio, photo, video, video_note, document, markup_text, application_name)
            VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            info
        )

        self.connection.commit()
        self.edit_steps_time(token=token, tg_id=tg_id, time=minutes)

    def get_steps_length(self, token):
        steps = self.cursor.execute(
            f"""
            SELECT step FROM steps 
            WHERE token='{token}'
            """
        ).fetchall()

        self.connection.commit()

        if steps is not None:
            return len(steps)
        return 0

    def get_user_step_number_and_time(self, tg_id: int, token: str):
        step_number = self.cursor.execute(
            """
            SELECT step_number, trigger_time FROM users_steps
            WHERE tg_id=?
            AND token=?
            """
        , (tg_id, token)).fetchone()

        self.connection.commit()
        return step_number[0], step_number[1]

    def get_steps_info(self, token: str):
        steps_info = self.cursor.execute(
            f"""
            SELECT step, minutes, step_number, audio, photo, video, video_note, document, markup_text, application_name FROM steps
            WHERE token='{token}'
            """
        ).fetchall()
        self.connection.commit()

        if steps_info is not None and len(steps_info) > 0:
            return steps_info
        return None

    def get_step_by_number(self, token: str, step_number: int):
        step_info = self.cursor.execute(
            f"""
            SELECT step, audio, photo, video, video_note, document, markup_text, application_name FROM steps
            WHERE step_number={step_number}
            AND token='{token}'
            """
        ).fetchone()
        self.connection.commit()
        #print(step_number, step_info)
        if step_info is None or any(step_info) is False:
            return None
        return step_info

    def get_steps(self, token: str):
        steps = self.cursor.execute(
            f"""
            SELECT step FROM steps
            WHERE token='{token}'
            """
        ).fetchall()
        self.connection.commit()

        if steps is not None and len(steps) > 0:
            steps = [step[0] for step in steps]
            return steps
        return None

    def delete_step(self, token: str, step_number: int):
        self.cursor.execute(
            f"""
            DELETE FROM steps
            WHERE step_number={step_number}
            AND token='{token}'
            """
        )

        self.connection.commit()

        self.minus_steps(token=token, step_number=step_number)
        self.minus_step_number(token=token, step_number=step_number)


    def minus_step_number(self, token: str, step_number: int):
        step = self.get_step_by_number(token=token, step_number=step_number + 1)
        step_numberr = step_number + 1
        print("minus number", token, step)
        if step is not None:
            while True:
                if step is None:
                    break

                self.cursor.execute(
                    f"""
                    UPDATE steps
                    SET step_number={step_numberr - 1}
                    WHERE token='{token}'
                    """
                )
                step_numberr += 1
                self.connection.commit()
                step = self.get_step_by_number(token=token, step_number=step_numberr)

    def get_users(self, token: str):
        users = self.cursor.execute(
            f"""
            SELECT tg_id, step_number FROM users_steps
            WHERE token='{token}'
            """
        ).fetchall()

        self.connection.commit()

        return users

    def minus_steps(self, token: str, step_number: int):
        users = self.get_users(token=token)

        if users is not None and len(users) > 0:
            steps_numbers = [user[1] for user in users]
            users = [user[0] for user in users]
            for user, step_numberr in zip(users, steps_numbers):
                if step_numberr - 2 == self.get_steps_length(token=token):
                    self.cursor.execute(
                        f"""
                        UPDATE users_steps
                        SET step_number={step_numberr - 1}
                        WHERE token='{token}'
                        AND tg_id={user}
                        """
                    )
                    self.connection.commit()

    def get_step_time(self, token: str, step_number: int):
        time = self.cursor.execute(
            f"""
            SELECT minutes FROM steps
            WHERE token='{token}'
            AND step_number={step_number}
            """
        ).fetchone()

        time = time[0]

        hours = time // 60
        minutes = time % 60

        return hours, minutes

    def edit_steps_time(self, token: str, tg_id: int, time: int):
        step_info = self.get_steps_info(token=token)
        #print(step_info)
        sorted_info = sorted(step_info, key=lambda x: x[1])
        #print(sorted_info)

        self.cursor.execute(
            f"""
            DELETE FROM steps
            WHERE token='{token}'
            """
        )

        num = 1
        for elem in sorted_info:
            if elem[1] == time:
                self.add_user_number(token=token, new_step_number=num)
                break
            num += 1

        count = 1
        for step, minutes, step_number, audio, photo, video, video_note, document, markup_text, application_name in sorted_info:
            info = (tg_id, token, step, minutes, count, audio, photo, video, video_note, document, markup_text, application_name)
            print(info)

            self.cursor.execute(
                f"""
                INSERT INTO steps
                (tg_id, token, step, minutes, step_number, audio, photo, video, video_note, document, markup_text, application_name)
                VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                info
            )
            count += 1

            self.connection.commit()

    def add_user_number(self, token: str, new_step_number: int):
        users = self.get_users(token=token)
        users = [user[0] for user in users]

        for tg_id in users:
            step_number, trigger_time = self.get_user_step_number_and_time(tg_id=tg_id, token=token)
            if step_number != new_step_number:
                self.add_or_update_user(token=token, tg_id=tg_id, step_number=step_number + 1, trigger_time=trigger_time)

    def delete_bot(self, token: str):
        tables_list = ["funnels", "users_steps", "triggers", "steps"]

        for name in tables_list:
            self.cursor.execute(
                f"""
                DELETE FROM {name}
                WHERE token='{token}'
                """
            )

            self.connection.commit()
