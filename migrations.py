# coding: utf-8

from database_api import SQLighter
import config

if __name__ == '__main__':
    db = SQLighter(config.database_name)
    db.set_up_tables()
