from functools import wraps
from flask import session, redirect, url_for


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session.get('logged_in'):
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))

    return wrap


def is_admin_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session.get('is_admin'):
            return f(*args, **kwargs)
        else:
            return "Only administrators can access it", 403

    return wrap
