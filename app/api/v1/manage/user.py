import json
from shortuuid import uuid
from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy import desc, asc
from sqlalchemy_pagination import paginate
from sqlalchemy import or_

from app.enums import ADMIN_KEY_GROUP
from app.extensions import db, logger
from flask_jwt_extended import jwt_required
from app.api.helper import send_result, send_error
from app.models import User, Group
from app.utils import trim_dict, escape_wildcard, get_timestamp_now
from app.validator import StaffValidation, QueryParamsSchema, QueryParamsAllSchema, UserSchema

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
@jwt_required
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

@api.route("", methods=["GET"])
def get_staff():
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = QueryParamsAllSchema().load(params) if params else dict()
        except ValidationError as err:
            logger.error(json.dumps({
                "message": err.messages,
                "data": err.valid_data
            }))
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)


        page = params.get('page', 1)
        page_size = params.get('page_size', 10)
        order_by = params.get('order_by', 'created_date')
        sort = params.get('sort', 'desc')
        text_search = params.get('text_search', None)

        query = User.query.filter(
                User.group.has(Group.is_staff == True),
                User.group.has(Group.key.notin_(ADMIN_KEY_GROUP)))


        if text_search:
            text_search = text_search.strip()
            text_search = text_search.lower()
            text_search = escape_wildcard(text_search)
            text_search = "%{}%".format(text_search)

            query = query.filter(
                or_(
                    User.full_name.ilike(f"%{text_search}%"),
                    User.email.ilike(f"%{text_search}%")
                )
            )

        column_sorted = getattr(User, order_by)

        query = query.order_by(desc(column_sorted)) if sort == "desc" else query.order_by(asc(column_sorted))

        paginator = paginate(query, page, page_size)

        staffs = UserSchema(many=True).dump(paginator.items)

        response_data = dict(
            items=staffs,
            total_pages=paginator.pages if paginator.pages > 0 else 1,
            total=paginator.total,
            has_previous=paginator.has_previous,
            has_next=paginator.has_next
        )
        return send_result(data=response_data)
    except Exception as ex:
        return send_error(message=str(ex))


