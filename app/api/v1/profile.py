import json
import uuid
from datetime import timedelta
from flask import Blueprint, request
from flask_jwt_extended import (get_jwt_identity, jwt_required)

from app.enums import ADMIN_EMAIL, MAIL_VERITY_CODE, GROUP_KEY_PARAM
from app.api.helper import get_permissions, CONFIG, send_email_template, get_roles_key, Token
from app.api.helper import send_error, send_result
from app.extensions import jwt, db
from app.models import User, EmailTemplate, VerityCode, Mail
from app.utils import trim_dict, get_timestamp_now, logged_input, data_preprocessing, generate_random_number_string, \
    body_mail
from app.extensions import mail

from app.validator import UserSchema


api = Blueprint('profile', __name__)


@api.route('/user', methods=['GET'])
@jwt_required
def profile():
    user_id = get_jwt_identity()
    user = User.query.filter(User.id == user_id).first()
    data = UserSchema().dump(user)

    data['param_router'] = GROUP_KEY_PARAM.get(user.group.key, '/')

    return send_result(data=data)


