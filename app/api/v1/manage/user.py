from shortuuid import uuid
from datetime import date

from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy import desc, asc, and_
from sqlalchemy_pagination import paginate
from sqlalchemy import or_

from app.enums import ADMIN_KEY_GROUP, KEY_GROUP_NOT_STAFF, USER_KEY_GROUP, TYPE_ACTION_SEND_MAIL
from app.extensions import db
from app.api.helper import send_result, send_error, convert_to_datetime, Token
from app.gateway import authorization_require
from app.message_broker import RabbitMQProducerSendMail
from app.models import User, Group, Files, Address
from app.settings import DevConfig
from app.utils import trim_dict, escape_wildcard, generate_password
from app.validator import StaffValidation, QueryParamsAllSchema, UserSchema, QueryStaffSchema
from app.extensions import mail
from flask_mail import Message as MessageMail

api = Blueprint('manage/user', __name__)


# Quan ly nhan vien
@api.route('', methods=['POST'])
@authorization_require()
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

        user = User(id=str(uuid()),**json_body)

        db.session.add(user)
        db.session.flush()
        db.session.commit()

        #send mail
        title_mail = f'CẤP TÀI KHOẢN C&N'
        html_content = f"""
                        <!DOCTYPE html>
                        <html lang="vi">
                        <head>
                            <meta charset="UTF-8">
                            <title>{title_mail}</title>
                        </head>
                        <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 0;">
                            <table align="center" width="100%" style="max-width: 600px; background-color: #ffffff; padding: 20px; border-radius: 8px;">
                                <tr>
                                    <td align="center" style="padding-bottom: 20px;">
                                        # <img src="{DevConfig.BASE_URL_WEBSITE}/logo.png" alt="C&N Fashion" style="height: 60px;">
                                        <img src="https://cc6b-1-55-188-41.ngrok-free.app/files/image/5382b5d6-d261-46a0-935f-602344dce9b7.jpg" alt="C&N Fashion" style="height: 60px;">

                                    </td>
                                </tr>
                                <tr>
                                    <td>
                                        <h2 style="color: #333333;"> <strong>C&N Fashion</strong>, xin chào {user.group.name}</h2>
                                        <p style="font-size: 16px; color: #555555;">
                                           Dưới đây là mật khẩu của bạn, không cung cấp cho người khác:
                                        </p>
                                        <div style="text-align: center; margin: 30px 0;">
                                            <span style="font-size: 32px; font-weight: bold; color: #2c3e50;">
                                                {user.password}
                                            </span>
                                        </div>
                                        <p style="font-size: 16px; color: #555555;">
                                            Trân trọng,<br>
                                            <strong>Đội ngũ C&N Fashion</strong>
                                        </p>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="center" style="font-size: 12px; color: #aaaaaa; padding-top: 20px;">
                                        © 2025 C&N Fashion. All rights reserved.<br>
                                        <a href="{DevConfig.BASE_URL_WEBSITE}" style="color: #aaaaaa;">cn.company.enterprise@gmail.com</a> | Hotline: 0988 951 321
                                    </td>
                                </tr>
                            </table>
                        </body>
                        </html>
                        """
        # gửi mail neu co queue
        body_mail = f"Xin chào {user.group.name} mới, mật khẩu của bạn là  {user.password}"
        if DevConfig.ENABLE_RABBITMQ_CONSUMER:
            body = {
                'type_action': TYPE_ACTION_SEND_MAIL['NEW_STAFF'],
                'body_mail': body_mail,
                'email': [email],
                'html': html_content,
                'title': title_mail
            }
            queue_mail = RabbitMQProducerSendMail()
            queue_mail.call(body)
        else:
            msg = MessageMail(title_mail, recipients=[email])
            msg.html = html_content
            mail.send(msg)

        return send_result(message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)

@api.route('/<profile_id>', methods=['GET'])
@authorization_require()
def profile_staff(profile_id):

    user = User.query.filter_by(id=profile_id).first()
    data = UserSchema().dump(user)
    return send_result(data=data)

@api.route('/<profile_id>', methods=['PUT'])
@authorization_require()
def update_staff(profile_id):

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

    if user.group_id != check_group.id:
        Token.revoke_all_token(user.id)


    for key, value in json_body.items():
        # Kiểm tra nếu trường đó tồn tại trong đối tượng User (tránh trường không hợp lệ)
        if hasattr(user, key):
            setattr(user, key, value)

        # Lưu thay đổi vào cơ sở dữ liệu
    db.session.commit()

    if user.finish_date and user.finish_date < date.today():
        Token.revoke_all_token(user.id)

    # Check finish date nếu hết hạn thì xóa token trển redis
    
    data=UserSchema().dump(user)

    return send_result(data=data, message='Thay đổi thông tin thành công')


@api.route("/active/<user_id>", methods=["PUT"])
@authorization_require()
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

        if not user.is_active:
            Token.revoke_all_token(user.id)

        # Xác định trạng thái mở/khoá
        status = "mở" if user.is_active else "khóa"
        return send_result(message=f"Tài khoản {user.email} đã được {status}.")

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))

@api.route("/staff", methods=["GET"])
@authorization_require()
def get_staff():
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = QueryStaffSchema().load(params) if params else dict()
        except ValidationError as err:
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)


        page = params.get('page', 1)
        page_size = params.get('page_size', 10)
        order_by = params.get('order_by', 'created_date')
        sort = params.get('sort', 'desc')
        text_search = params.get('text_search', None)
        type_staff = params.get('type_staff', None)

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

        if type_staff == 'work_on':
            query = query.filter(
                or_(
                    User.finish_date == None,
                    User.finish_date >= date.today()
                )
            )
        elif type_staff == 'work_off':
            query = query.filter(
                and_(
                    User.finish_date != None,
                    User.finish_date < date.today()
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
@authorization_require()
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
@authorization_require()
def remove_item():
    try:
        body_request = request.get_json()
        list_id = body_request.get('list_id', [])
        if len(list_id) == 0:
            return send_error(message='Chưa chọn item nào.')
        User.query.filter(User.id.in_(list_id)).delete()
        db.session.flush()
        db.session.commit()
        return send_result(message="Xóa thành công")
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))


