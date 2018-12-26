# coding: utf-8
from functools import wraps
from credentials import ALLOWED_USERS_IDS


def authorise(func):
    @wraps(func)
    def wrap(call, *args, **kwargs):
        if call.from_user.id not in ALLOWED_USERS_IDS:
            return
        else:
            return func(call, *args, **kwargs)
    return wrap
