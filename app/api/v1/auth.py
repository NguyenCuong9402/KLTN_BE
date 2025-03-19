import json
from datetime import timedelta

from shortuuid import uuid
from flask import Blueprint, request
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                get_jwt_identity, get_raw_jwt, jwt_refresh_token_required, jwt_required)
from werkzeug.security import check_password_hash, generate_password_hash

from app.enums import ADMIN_EMAIL, MAIL_VERITY_CODE, GROUP_KEY_PARAM, GROUP_ADMIN_KEY, GROUP_USER_KEY
from app.api.helper import get_permissions, CONFIG, send_email_template, get_roles_key, Token, convert_to_datetime
from app.api.helper import send_error, send_result, Token
from app.extensions import jwt, db
from app.gateway import authorization_require
from app.models import User, EmailTemplate, VerityCode, Mail, GroupRole, Group, Address
from app.utils import trim_dict, get_timestamp_now, logged_input, data_preprocessing, generate_random_number_string, \
    body_mail
from app.extensions import mail

from app.validator import UserSchema, AuthValidation, PasswordValidation, EmailValidation, VerifyPasswordValidation, \
    RegisterValidation, ProductValidation, UserValidation
from flask_mail import Message as MessageMail

ACCESS_EXPIRES = timedelta(days=7)
REFRESH_EXPIRES = timedelta(days=7)
api = Blueprint('auth', __name__)

# Message_ID variable
INVALID_EMAIL = '001'
INCORRECT_EMAIL_PASSWORD = "002"
INACTIVE_ACCOUNT_ERROR = "003"
INVALID_PASSWORD = '004'
CHANGE_DEFAULT_PASS_SUCCESS = '006'
CHANGE_DEFAULT_PASS_SUCCESS_USER_SITE = '198'
EMAIL_NOT_EXISTED = '007'
SUPER_ADMIN_EMAIL_ERROR = '009'
FORGOT_PASSWORD_TOO_MANY = '010'
INCORRECT_PASSWORD = '030'
YOU_DO_NOT_HAVE_PERMISSION = '164'


@api.route('/login', methods=['POST'])
def login():
    try:
        json_req = request.get_json()
    except Exception as ex:
        return send_error(message="Request Body incorrect json format: " + str(ex), code=442)

    # trim input body
    json_body = trim_dict(json_req)

    # validate request body
    is_valid, message_id = data_preprocessing(cls_validator=AuthValidation, input_json=json_req)
    if not is_valid:
        return send_error(message_id=message_id)

    # Check username and password
    email = json_body.get("email")
    password = json_body.get("password")

    user = User.query.filter(User.email == email).first()
    # if user is None or (password and not check_password_hash(user.password_hash, password)):
    #     return send_error(message_id=INCORRECT_EMAIL_PASSWORD)

    if user is None:
        return send_error(message='Tài khoản không tồn tại.')

    if user.password != password:
        return send_error(message='Mật khẩu không đúng.')

    # user_roles = get_roles_key(user)

    # Check permission login (from user/admin side?)
    if not user.is_active:
        return send_error(message='Tài khoản đang bị khóa')

    # list_permission = get_permissions(user)

    access_token = create_access_token(identity=user.id, expires_delta=ACCESS_EXPIRES, )
    refresh_token = create_refresh_token(identity=user.id, expires_delta=REFRESH_EXPIRES)

    # Store the tokens in our store with a status of not currently revoked.
    # Token.add_token_to_database(access_token, user.id)
    # Token.add_token_to_database(refresh_token, user.id)
    # Token.add_list_permission(user.id, list_permission)

    data: dict = UserSchema().dump(user)
    data.setdefault('access_token', access_token)
    data.setdefault('refresh_token', refresh_token)
    data.setdefault('param_router', GROUP_KEY_PARAM.get(user.group.key, '/'))

    return send_result(data=data)


@api.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    """
    This api use for refresh expire time of the access token. Please inject the refresh token in Authorization header

    Requests Body:

        refresh_token: string,require
        The refresh token return to the login API

    Returns:

        access_token: string
        A new access_token

    Examples::

    """

    user_identity = get_jwt_identity()
    user = User.get_by_id(user_identity)

    list_permission = get_permissions(user)
    access_token = create_access_token(identity=user.id)

    # Store the tokens in our store with a status of not currently revoked.
    Token.add_token_to_database(access_token, user_identity)
    Token.add_list_permission(user.id, list_permission)

    data = {
        'access_token': access_token
    }

    return send_result(data=data)


@api.route('/logout', methods=['DELETE'])
@jwt_required
def logout():
    """
    This api logout current user, revoke current access token

    Examples::

    """

    jti = get_raw_jwt()['jti']
    Token.revoke_token(jti)  # revoke current token from database

    return send_result(message="Logout successfully!")


@api.route('/register', methods=['POST'])
def register():
    try:

        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = RegisterValidation()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')

        if json_body.get('password') != json_body.get('confirm_password'):
            return send_error(message='Confirm password khác password.')

        json_body.pop('confirm_password')
        if User.query.filter(User.email == json_body.get('email'), User.phone == json_body.get('phone')).first():
            return send_error(message='Gmail/ Phone đã được đăng ký.')
        group = Group.query.filter(Group.key == GROUP_USER_KEY).first()
        user = User(id=str(uuid()), **json_body, group_id=group.id)
        db.session.add(user)
        db.session.flush()

        code = generate_random_number_string()
        # body = body_mail(MAIL_VERITY_CODE, {'code': code})
        body = f"Mã Code của bạn là : {code} "
        # Mail
        mail_send = Mail(id=str(uuid()), body=body, email=json_body.get('email'))

        db.session.add(mail_send)
        db.session.flush()

        # Tạo verity code
        code = VerityCode(id=str(uuid()), user_id=user.id, mail_id=mail_send.id, code=code, type=1)
        db.session.add(code)
        db.session.flush()

        # gửi mail
        msg = MessageMail('Mã xác thực:', recipients=[json_body.get('email')])
        msg.body = mail_send.body
        mail.send(msg)

        db.session.commit()
        return send_result(data={'verity_code_id': code.id}, message='Đăng kí thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


@api.route('/send_code', methods=['POST'])
@jwt_required
def send_code():
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            send_error(message='Người dùng không hợp lệ.')

        code = generate_random_number_string()
        # body = body_mail(MAIL_VERITY_CODE, {'code': code})
        body = f"Mã Code của bạn là : {code} "
        # Mail
        mail_send = Mail(id=str(uuid()), body=body, email=user.email)

        db.session.add(mail_send)
        db.session.flush()

        # Tạo verity code
        code = VerityCode(id=str(uuid()), user_id=user.id, mail_id=mail_send.id, code=code, type=1)
        db.session.add(code)

        db.session.flush()
        db.session.commit()

        msg = MessageMail('Mã xác thực là:', recipients=[user.email])
        msg.body = mail_send.body
        mail.send(msg)

        return send_result(message='Gửi Code thành công.', data={'verity_code_id': code.id})
    except Exception as ex:
        db.session.rollback()
        return send_error(message="Error" + str(ex), code=442)



@api.route('/change_password', methods=['PUT'])
@jwt_required
def change_password():
    try:
        user_id = get_jwt_identity()
        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = PasswordValidation()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')

        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message="Người dùng không hợp lệ")

        current_password = json_body.get('current_password')
        new_password = json_body.get('new_password')
        confirm_password = json_body.get('confirm_password')

        if current_password != user.password:
            return send_error(message='Mật khẩu cũ không đúng.')

        if new_password != confirm_password:
            return send_error(message='Xác nhận mật khẩu chưa đúng. ')

        user.password = new_password
        db.session.flush()
        db.session.commit()
        data =  UserSchema().dump(user)

        return send_result(data=data, message='Đổi mật khẩu thành công')
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


@api.route('/verity_code', methods=['POST'])
def verity_code():
    try:
        json_req = request.get_json()
        # user_id = get_jwt_identity()
        code = json_req.get('code', '')
        verity_code_id = json_req.get('verity_code_id', '')
        verity = VerityCode.query.filter(VerityCode.id == verity_code_id).first()
        if verity.code != code:
            return send_error(message='Mã Code không hợp lệ.')
        user = User.query.filter(User.id == verity.user_id).first()
        user.is_active = 1
        db.session.flush()
        db.session.commit()
        return send_result(message='Xác thực thành công.')
    except Exception as ex:
        db.session.rollback()
        return send_error(message="Error" + str(ex), code=442)


@jwt.token_in_blacklist_loader
def check_if_token_is_revoked(decrypted_token):
    """
    :param decrypted_token:
    :return:
    """
    return Token.is_token_revoked(decrypted_token)


@jwt.expired_token_loader
def expired_token_callback():
    """
    The following callbacks are used for customizing jwt response/error messages.
    The original ones may not be in a very pretty format (opinionated)
    :return:
    """
    return send_error(code=401, message_id='SESSION_TOKEN_EXPIRED', message='Token hết hạn')


@jwt.revoked_token_loader
def revoked_token_callback():
    return send_error(code=401, message_id='SESSION_TOKEN_EXPIRED', message='Token hết hạn')


# @jwt.token_in_blacklist_loader
# def check_if_token_is_revoked(decrypted_token):
#     """
#     :param decrypted_token:
#     :return:
#     """
#     return Token.is_token_revoked(decrypted_token)

### Để tạm
jwt_blocklist = set()

# Kiểm tra nếu token nằm trong blocklist
@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token["jti"]
    return jti in jwt_blocklist
