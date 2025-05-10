import pickle
from functools import wraps

from flask import request
from flask_jwt_extended import (
    verify_jwt_in_request, get_jwt_claims, get_jwt_identity
)

from app.api.helper import send_error
from app.extensions import red


def authorization_require():
    """
    validate authorization follow permission user
    Args:

    Returns:

    """

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            permission_route = "{0}@{1}".format(request.method.lower(), request.url_rule.rule)
            # claims = get_jwt_claims()
            #
            # if claims.get("force_change_password"):
            #     return send_error(message='You have to change your password before do this action')

            # check permission from redis
            list_permission = pickle.loads(red.get(f"permission_{get_jwt_identity()}"))
            if permission_route in list_permission:
                return fn(*args, **kwargs)
            else:
                return send_error(message='BẠN KHÔNG CÓ QUYỀN')

        return decorator

    return wrapper
