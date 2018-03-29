# coding: utf-8
import sqlite3
import config


class SQLighter:

    def __init__(self, database):
        self.connection = sqlite3.connect(config.database_name)
        self.cursor = self.connection.cursor()

    def set_up_tables(self):
        """ Начальная миграция """
        with self.connection:
            from bot import PURCHASES
            self.cursor.execute('CREATE TABLE IF NOT EXISTS finance (id integer PRIMARY KEY,user_id text NOT NULL,message_id text NOT NULL,message_timestamp integer NOT NULL,expense text,prise text NOT NULL,note text NOT NULL);')
            self.cursor.execute('CREATE TABLE IF NOT EXISTS expenses (id integer PRIMARY KEY, expense text NOT NULL);')
            for expense in PURCHASES:
                self.cursor.execute('INSERT INTO expenses (expense) VALUES (?);', (expense,))

    def record_item(self, user_id, message_id, message_timestamp, prise, note):
        """ Запишем расход в БД """
        with self.connection:
            self.cursor.execute(
                u"""INSERT INTO finance 
                    (user_id, message_id, message_timestamp, expense, prise, note) 
                    VALUES (?, ?, ?, ?, ?, ?);""",
                (user_id, message_id, message_timestamp, None, prise, note)
            )

    def find_expense(self, note):
        return self.cursor.execute(
            'SELECT DISTINCT expense from finance WHERE note=? AND expense IS NOT NULL;', (note,)
        ).fetchall()

    def update_expense(self, message_id, expense):
        with self.connection:
            self.cursor.execute('UPDATE finance SET expense=? WHERE message_id=?;', (expense, message_id))

    def stat_by_total_month(self, month_ts):
        with self.connection:
            return self.cursor.execute(
                'SELECT SUM(prise) from finance WHERE message_timestamp > ?;', (month_ts,)
            ).fetchall()[0][0]

    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()
