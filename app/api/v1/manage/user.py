import json
from shortuuid import uuid
from datetime import datetime, date, time

from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy import desc, asc
from sqlalchemy_pagination import paginate
from sqlalchemy import or_
from sqlalchemy import extract

from app.enums import ADMIN_KEY_GROUP, KEY_GROUP_NOT_STAFF, ATTENDANCE, USER_KEY_GROUP
from app.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.helper import send_result, send_error, convert_to_datetime
from app.models import User, Group, Files, Address, Attendance
from app.utils import trim_dict, escape_wildcard, get_timestamp_now, generate_password
from app.validator import StaffValidation, QueryParamsAllSchema, UserSchema, AttendanceSchema

api = Blueprint('manage/user', __name__)


# Quan ly nhan vien
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


        email = json_body.get('email')
        phone = json_body.get('phone')
        group_id = json_body.get('group_id')
        avatar_id = json_body.get('avatar_id', None)

        address = json_body.pop('address')
        if json_body.get('birthday', None):
            json_body['birthday'] = convert_to_datetime(json_body.get('birthday'))

        for key, value in address.items():
            if value is None or value.strip() == '':
                return send_error(message='Vui lòng chọn địa chỉ')

        address = Address.query.filter_by(province=address.get('province'), district=address.get('district'),
                                          ward=address.get('ward')).first()
        if address is None:
            return send_error(message="Địa chỉ không hợp lệ.")

        json_body['address_id'] = address.id


        check_email = User.query.filter_by(email=email).first()
        if check_email:
            return send_error(message='Email đã được đăng ký')

        check_phone = User.query.filter_by(phone=phone).first()
        if check_phone:
            return send_error(message='SĐT đã được đăng ký')

        check_group = Group.query.filter_by(id=group_id).first()
        if check_group is None:
            return send_error(message='Chức vụ không tồn tại')

        if check_group.key in KEY_GROUP_NOT_STAFF:
            return send_error(message='Chức vụ không phù hợp')

        if avatar_id:
            check_file = Files.query.filter_by(id=avatar_id).first()
            if check_file is None:
                return send_error(message='Vui lòng tải lại ảnh')

        json_body['password'] = generate_password()

        json_body['status'] = 0 # Khi nào User đăng nhập sẽ được kích hoạt
        user = User(id=str(uuid()),**json_body)

        db.session.add(user)
        db.session.flush()
        db.session.commit()

        #send mail

        return send_result(message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)

@api.route('/<profile_id>', methods=['GET'])
@jwt_required
def profile_staff(profile_id):

    user = User.query.filter_by(id=profile_id).first()
    data = UserSchema().dump(user)
    return send_result(data=data)

@api.route('/<profile_id>', methods=['PUT'])
@jwt_required
def update_staff(profile_id):

    body = request.get_json()
    json_req = request.get_json()
    json_body = trim_dict(json_req)
    validator_input = StaffValidation()
    is_not_validate = validator_input.validate(json_body)
    if is_not_validate:
        return send_error(data=is_not_validate, message='Validate Error')

    user = User.query.filter(User.id==profile_id, User.group.has(is_staff=True)).first()
    if user is None:
        return send_error(message='Nhân viên không tồn tại')
    address = json_body.pop('address')
    address = Address.query.filter_by(province=address.get('province'), district=address.get('district'),
                                      ward=address.get('ward')).first()
    if address is None:
        return send_error(message="Địa chỉ không hợp lệ.")

    json_body['address_id'] = address.id

    check_email = User.query.filter(User.email==json_body['email'], User.id!=user.id).first()
    if check_email:
        return send_error(message='Email đã được đăng ký')

    check_phone = User.query.filter(User.phone == json_body['phone'], User.id != user.id).first()
    if check_phone:
        return send_error(message='SĐT đã được đăng ký')

    check_group = Group.query.filter_by(id=json_body['group_id']).first()
    if check_group is None:
        return send_error(message='Chức vụ không tồn tại')

    if check_group.key in KEY_GROUP_NOT_STAFF:
        return send_error(message='Chức vụ không phù hợp')

    for key, value in json_body.items():
        # Kiểm tra nếu trường đó tồn tại trong đối tượng User (tránh trường không hợp lệ)
        if hasattr(user, key):
            setattr(user, key, value)

        # Lưu thay đổi vào cơ sở dữ liệu
    db.session.commit()
    
    data=UserSchema().dump(user)

    return send_result(data=data, message='Thay đổi thông tin thành công')


@api.route("/active/<user_id>", methods=["PUT"])
@jwt_required
def active_user(user_id):
    try:
        user = User.query.filter(User.id == user_id).first()
        if not user:
            return send_error(message="Người dùng không tồn tại!")

        # Đảo trạng thái active
        user.is_active = not user.is_active
        db.session.flush()
        db.session.refresh(user)
        db.session.commit()

        # Xác định trạng thái mở/khoá
        status = "mở" if user.is_active else "khóa"
        return send_result(message=f"Tài khoản {user.email} đã được {status}.")

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))

@api.route("/staff", methods=["GET"])
@jwt_required
def get_staff():
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = QueryParamsAllSchema().load(params) if params else dict()
        except ValidationError as err:
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)


        page = params.get('page', 1)
        page_size = params.get('page_size', 10)
        order_by = params.get('order_by', 'created_date')
        sort = params.get('sort', 'desc')
        text_search = params.get('text_search', None)

        query = User.query.join(Group).filter(
            Group.is_staff == True,
            Group.key.notin_(ADMIN_KEY_GROUP)
        )


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

        if order_by == "group_name":
            column_sorted = Group.name  # Thay vì User.group.name
        else:
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


@api.route("/customer", methods=["GET"])
@jwt_required
def get_customer():
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = QueryParamsAllSchema().load(params) if params else dict()
        except ValidationError as err:
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)


        page = params.get('page', 1)
        page_size = params.get('page_size', 10)
        order_by = params.get('order_by', 'created_date')
        sort = params.get('sort', 'desc')
        text_search = params.get('text_search', None)

        query = User.query.join(Group).filter(
            Group.is_staff == False, Group.is_super_admin == False,
            Group.key == USER_KEY_GROUP
        )


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

        customers = UserSchema(many=True).dump(paginator.items)

        response_data = dict(
            items=customers,
            total_pages=paginator.pages if paginator.pages > 0 else 1,
            total=paginator.total,
            has_previous=paginator.has_previous,
            has_next=paginator.has_next
        )
        return send_result(data=response_data)
    except Exception as ex:
        return send_error(message=str(ex))


@api.route("", methods=["DELETE"])
@jwt_required
def remove_item():
    try:
        body_request = request.get_json()
        list_id = body_request.get('list_id', [])
        if len(list_id) == 0:
            return send_error(message='Chưa chọn item nào.')
        User.query.filter(User.id.in_(list_id)).delete()
        db.session.flush()
        db.session.commit()
        return send_result(message="Xóa sản phẩm thành công")
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))


