# coding: utf-8
import sqlite3
import config


class SQLighter:

    def __init__(self):
        self.connection = sqlite3.connect(config.database_name)
        self.cursor = self.connection.cursor()

    def set_up_tables(self):
        """ Начальная миграция """
        with self.connection:
            self.connection.executescript(u"""
                
                CREATE TABLE IF NOT EXISTS finance (
                id integer PRIMARY KEY,
                user_id text NOT NULL,
                message_id text NOT NULL,
                message_timestamp integer NOT NULL,
                expense text,
                prise text NOT NULL,
                note text NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS expenses (
                id integer PRIMARY KEY, 
                expense text NOT NULL
                );
                
                
            """)
            self.cursor.executemany('INSERT INTO expenses (expense) VALUES (?);', config.EXPENSES)

    def record_item(self, user_id, message_id, message_timestamp, prise, note, expense):
        """ Запишем расход в БД """
        with self.connection:
            self.cursor.execute(
                u"""
                  INSERT INTO finance 
                  (user_id,
                  message_id,
                  message_timestamp,
                  expense,
                  prise,
                  note)
                  VALUES (?, ?, ?, ?, ?, ?);
                    """,
                (user_id, message_id, message_timestamp, expense, prise, note)
            )

    def delete_expense_by_message_id(self, message_id, text=None):
        with self.connection:
            if not text:
                self.cursor.execute(
                    u"""DELETE FROM finance WHERE message_id=?;""", (message_id,)
                )
            else:
                self.cursor.execute(
                    u"""DELETE FROM finance WHERE message_id=? and note=?;""", (message_id, text)
                )

    def find_expense_by_timestamp(self, message_timestamp):
        with self.connection:
            return self.cursor.execute(
                u"""SELECT expense from finance WHERE message_timestamp=? AND expense IS NOT NULL LIMIT 1;""",
                (message_timestamp,)
            ).fetchone()

    def find_expense(self, note):
        with self.connection:
            return self.cursor.execute(
                u"""SELECT DISTINCT expense from finance WHERE note=? AND expense IS NOT NULL;""",
                (note,)
            ).fetchone()

    def update_expense(self, message_id, expense, text=None):
        if not text:
            with self.connection:
                self.cursor.execute(
                    u"""UPDATE finance SET expense=? WHERE message_id=?;""",
                    (expense, message_id)
                )
        else:
            with self.connection:
                self.cursor.execute(
                    u"""UPDATE finance SET expense=? WHERE message_id=? and note=?;""",
                    (expense, message_id, text)
                )

    def stat_by_total_month(self, month_ts):
        with self.connection:
            return self.cursor.execute(
                u"""SELECT SUM(prise) from finance WHERE message_timestamp > ? and expense != 11;""",
                (month_ts,)
            ).fetchone()
