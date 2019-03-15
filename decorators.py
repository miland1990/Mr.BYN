# coding: utf-8
from logg import logger
from functools import wraps
from credentials import ALLOWED_USERS_IDS
from database import db_make_session


def authorise(func):
    @wraps(func)
    def wrap(call, *args, **kwargs):
        if call.from_user.id not in ALLOWED_USERS_IDS:
            logger.info('forbidden user {}'.format(call.from_user.id))
            return
        else:
            return func(call, *args, **kwargs)
    return wrap


def wrap_to_session(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        session = db_make_session()
        func_result = func(session, *args, **kwargs)
        session.commit()
        session.close()
        return func_result
    return wrap


def logg(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        func_result = func(*args, **kwargs)
        msg = args[1]
        if 'callback' in func.__name__:
            logger.info(msg.message.text + ' - ' + msg.data)
        else:
            logger.info(msg.text)
        return func_result
    return wrap
