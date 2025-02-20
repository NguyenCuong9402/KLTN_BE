import json
import uuid
from datetime import timedelta
from flask import Blueprint, request
from flask_jwt_extended import (get_jwt_identity, jwt_required)

from app.enums import  GROUP_KEY_PARAM
from app.api.helper import get_permissions, CONFIG, send_email_template, get_roles_key, Token, convert_to_datetime
from app.api.helper import send_error, send_result
from app.extensions import jwt, db
from app.models import User, EmailTemplate, VerityCode, Mail, Address
from app.utils import trim_dict, get_timestamp_now, logged_input, data_preprocessing, generate_random_number_string, \
    body_mail
from app.extensions import mail

from app.validator import UserSchema, UserValidation

api = Blueprint('profile', __name__)


@api.route('', methods=['GET'])
@jwt_required
def profile():
    user_id = get_jwt_identity()
    user = User.query.filter(User.id == user_id).first()
    data = UserSchema().dump(user)

    data['param_router'] = GROUP_KEY_PARAM.get(user.group.key, '/')

    return send_result(data=data)

@api.route('', methods=['PUT'])
@jwt_required
def update_profile():
    try:
        user_id = get_jwt_identity()
        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = UserValidation()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')

        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message="Người dùng không hợp lệ")

        address = json_body.pop('address')
        if json_body.get('birthday', None):
            json_body['birthday'] = convert_to_datetime(json_body.get('birthday'))

        for key, value in address.items():
            if value is None or value.strip() =='':
                return send_error(message='Vui lòng chọn địa chỉ')

        address = Address.query.filter_by(province=address.get('province'), district=address.get('district'),
                                          ward=address.get('ward')).first()
        if address is None:
            return send_error(message="Địa chỉ không hợp lệ.")
        user.address_id = address.id

        for key, value in json_body.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)

        db.session.flush()
        db.session.commit()
        data =  UserSchema().dump(user)
        data.setdefault('param_router', GROUP_KEY_PARAM.get(user.group.key, '/'))

        return send_result(data=data, message='Thành công')
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


