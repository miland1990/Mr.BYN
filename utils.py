# coding: utf-8
from credentials import ALLOWED_USERS_IDS
from functools import wraps


def authorise(func):
    @wraps(func)
    def wrap(call, *args, **kwargs):
        if call.from_user.id not in ALLOWED_USERS_IDS:
            return
        else:
            return func(call, *args, **kwargs)
    return wrap
