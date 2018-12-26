# coding: utf-8
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


def get_engine():
    return create_engine('sqlite+pysqlite:///finance.db')


def db_make_session():
    db_create_tables()
    session = sessionmaker(bind=get_engine(), autoflush=False)
    return session()


def db_create_tables():
    """
    Перед началом работы бота следует запустить, чтобы создались таблицы БД.
    """
    # импортируем сюда модели
    from models import Purchase, Conversation, ExpenseCategory
    engine = get_engine()
    Base.metadata.create_all(engine)
