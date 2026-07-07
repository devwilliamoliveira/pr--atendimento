from functools import wraps

from flask import abort
from flask_login import current_user


def requer_papel(*papeis_permitidos):
    """Decorator para views web: exige que o usuário logado tenha um dos papéis informados."""

    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.papel not in papeis_permitidos:
                abort(403)
            return f(*args, **kwargs)

        return wrapper

    return decorador
