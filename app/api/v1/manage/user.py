import json
from shortuuid import uuid
from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy import desc, asc
from sqlalchemy_pagination import paginate

from app.extensions import db
from flask_jwt_extended import jwt_required
from app.api.helper import send_result, send_error
from app.models import User
from app.utils import trim_dict, escape_wildcard, get_timestamp_now
from app.validator import StaffValidation

api = Blueprint('manage/user', __name__)


@api.route('', methods=['POST'])
@jwt_required
def new():
    try:

        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = StaffValidation()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')


        db.session.flush()

        db.session.commit()
        return send_result(message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)



@api.route("/<user_id>", methods=["PUT"])
@jwt_required()
def active_user(user_id):
    try:
        user = User.query.filter(User.id == user_id).first()
        if not user:
            return send_error(message="Người dùng không tồn tại!")

        # Đảo trạng thái active
        user.active = not user.active
        db.session.flush()
        db.session.refresh(user)  # Cập nhật trạng thái mới sau flush()
        db.session.commit()

        # Xác định trạng thái mở/khoá
        status = "mở" if user.active else "khóa"
        return send_result(message=f"Tài khoản {user.email} đã được {status}.")

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))

