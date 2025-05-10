import json
from datetime import timedelta, datetime

from shortuuid import uuid
from flask import Blueprint, request
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                get_jwt_identity, get_raw_jwt, jwt_refresh_token_required, jwt_required)
from werkzeug.security import check_password_hash, generate_password_hash

from app.enums import GROUP_KEY_PARAM, GROUP_ADMIN_KEY, GROUP_USER_KEY, \
    TYPE_ACTION_SEND_MAIL
from app.api.helper import get_permissions, CONFIG, send_email_template, get_roles_key, Token, convert_to_datetime, \
    get_user_id_request
from app.api.helper import send_error, send_result, Token
from app.extensions import jwt, db
from app.gateway import authorization_require
from app.message_broker import RabbitMQProducerSendMail
from app.models import User, VerityCode, Group
from app.settings import DevConfig
from app.utils import trim_dict, get_timestamp_now, data_preprocessing, generate_random_number_string
from app.extensions import mail

from app.validator import UserSchema, AuthValidation, PasswordValidation, RegisterValidation
from flask_mail import Message as MessageMail

ACCESS_EXPIRES = timedelta(days=1)
REFRESH_EXPIRES = timedelta(days=31)
# ACCESS_EXPIRES = timedelta(seconds=30)
# REFRESH_EXPIRES = timedelta(minutes=2)

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

    if not user.status:
        return send_error(message='Tài khoản không tồn tại')

    if user.password != password:
        return send_error(message='Mật khẩu không đúng.')

    # user_roles = get_roles_key(user)

    # Check permission login (from user/admin side?)
    if not user.is_active:
        return send_error(message='Tài khoản đang bị khóa')

    if user.group.is_staff:
        current_date = datetime.now().date()
        # Kiểm tra xem finish_date có >= ngày hiện tại không
        if user.join_date  and user.join_date  >= current_date:
            return send_error(message='Tài khoản chưa đến ngày làm việc.')
        if user.finish_date:
            if user.finish_date <= current_date:
                return send_error(message='Tài khoản đã hết thời gian làm việc.')
    list_permission = get_permissions(user)

    access_token = create_access_token(identity=user.id, expires_delta=ACCESS_EXPIRES, )
    refresh_token = create_refresh_token(identity=user.id, expires_delta=REFRESH_EXPIRES)

    # Store the tokens in our store with a status of not currently revoked.
    Token.add_token_to_database(access_token, user.id)
    Token.add_token_to_database(refresh_token, user.id)
    Token.add_list_permission(user.id, list_permission)

    data: dict = UserSchema().dump(user)
    data.setdefault('access_token', access_token)
    data.setdefault('refresh_token', refresh_token)

    if user.group.is_super_admin:
        data.setdefault('param_router', GROUP_KEY_PARAM.get("is_supper_admin", '/'))
    elif user.group.is_staff:
        data.setdefault('param_router', GROUP_KEY_PARAM.get("is_staff", '/'))

    else:
        data.setdefault('param_router', GROUP_KEY_PARAM.get("user", '/'))


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

    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()

    # list_permission = get_permissions(user)
    access_token = create_access_token(identity=user.id, expires_delta=ACCESS_EXPIRES, )

    # # Store the tokens in our store with a status of not currently revoked.
    # Token.add_token_to_database(access_token, user_identity)
    # Token.add_list_permission(user.id, list_permission)

    data = {
        'access_token': access_token
    }

    return send_result(data=data)


@api.route('/logout', methods=['DELETE'])
@authorization_require()
def logout():
    """
    This api logout current user, revoke current access token

    Examples::

    """

    jti = get_raw_jwt()['jti']
    Token.revoke_token(jti)

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
        if User.query.filter(User.email == json_body.get('email'), User.status == 1).first():
            return send_error(message='Gmail đã được đăng ký.')
        User.query.filter(User.email == json_body.get('email'), User.status == 0).delete()
        group = Group.query.filter(Group.key == GROUP_USER_KEY).first()
        user = User(id=str(uuid()), **json_body, group_id=group.id, status=False, is_active=True, user_tele_id=str(uuid()))
        db.session.add(user)
        db.session.flush()

        email = json_body.get('email')
        code = generate_random_number_string()
        # body = body_mail(MAIL_VERITY_CODE, {'code': code})
        body = f"Mã Code của bạn là : {code} "
        # Mail

        # Tạo verity code
        code = VerityCode(id=str(uuid()), user_id=user.id, code=code, limit=get_timestamp_now() + 5 * 60)
        db.session.add(code)
        db.session.flush()

        title_mail = 'MÃ XÁC THỰC ĐĂNG KÝ TÀI KHOẢN C&N'
        # gửi mail neu co queue
        if DevConfig.ENABLE_RABBITMQ_CONSUMER:
            body = {
                'type_action': TYPE_ACTION_SEND_MAIL['REGISTER'],
                'body_mail': body,
                'email': [email],
                'title': title_mail
            }
            queue_mail = RabbitMQProducerSendMail()
            queue_mail.call(body)
        else:
            msg = MessageMail(title_mail, recipients=[email])
            msg.body = body
            mail.send(msg)

        db.session.commit()
        return send_result(data={'verity_code_id': code.id}, message='Đăng kí thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


@api.route('/send_code', methods=['POST'])
def send_code():
    try:
        json_req = request.get_json()

        type_input_code = json_req.get('type_input_code', None)
        email = json_req.get('email', None)


        user_id = get_user_id_request()

        if user_id:
            user = User.query.filter_by(id=user_id).first()
            email = user.email
        else:
            if type_input_code == TYPE_ACTION_SEND_MAIL['REGISTER'] and not email.strip():
                return send_error(message='Bạn chưa nhập email')
            user = User.query.filter_by(email=email).first()
            user_id = user.id


        code = generate_random_number_string()
        # body = body_mail(MAIL_VERITY_CODE, {'code': code})
        body = f"Mã Code của bạn là : {code} "
        # Tạo verity code
        code = VerityCode(id=str(uuid()), user_id=user_id, code=code, limit=get_timestamp_now() + 5 * 60)
        db.session.add(code)

        db.session.flush()
        db.session.commit()

        # msg = MessageMail('Mã xác thực là:', recipients=[user.email])
        # msg.body = mail_send.body
        # mail.send(msg)

        title_mail = 'MÃ XÁC THỰC'

        if type_input_code == TYPE_ACTION_SEND_MAIL['OPEN_ACCOUNT']:
            title_mail = 'MÃ XÁC THỰC MỞ KHÓA TÀI KHOẢN C&N'

        elif type_input_code == TYPE_ACTION_SEND_MAIL['UPDATE_ACCOUNT']:
            title_mail = 'MÃ XÁC THAY ĐỔI MẬT KHẨU TÀI KHOẢN C&N'

        elif type_input_code == TYPE_ACTION_SEND_MAIL['REGISTER']:
            title_mail = 'MÃ XÁC THAY ĐỔI MẬT KHẨU TÀI KHOẢN C&N'

        if DevConfig.ENABLE_RABBITMQ_CONSUMER:
            body = {
                'type_action': type_input_code,
                'body_mail': body,
                'email': [email],
                'title': title_mail
            }
            queue_mail = RabbitMQProducerSendMail()
            queue_mail.call(body)
        else:
            msg = MessageMail(title_mail, recipients=[email])
            msg.body = body
            mail.send(msg)

        return send_result(message='Gửi Code thành công.', data={'verity_code_id': code.id})
    except Exception as ex:
        db.session.rollback()
        return send_error(message="Error" + str(ex), code=442)



@api.route('/change_password', methods=['PUT'])
@authorization_require()
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
        user_id = get_user_id_request()
        code = json_req.get('code', '')
        verity_code_id = json_req.get('verity_code_id', '')
        type_input_code = json_req.get('type_input_code', None)
        verity = VerityCode.query.filter(VerityCode.id == verity_code_id).first()

        if verity is None:
            return send_error('Không tìm thấy mã xác thực')

        if verity and verity.limit:
            if verity.limit < get_timestamp_now():
                return send_error(message='Code đã hết hạn')
        if verity.code != code:
            return send_error(message='Mã Code không hợp lệ.')

        if type_input_code == TYPE_ACTION_SEND_MAIL['REGISTER']:
            user = User.query.filter(User.id == verity.user_id).first()
            user.status = 1
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


@jwt.token_in_blacklist_loader
def check_if_token_is_revoked(decrypted_token):
    """
    :param decrypted_token:
    :return:
    """
    return Token.is_token_revoked(decrypted_token)

# ### Để tạm
# jwt_blocklist = set()
#
# # Kiểm tra nếu token nằm trong blocklist
# @jwt.token_in_blacklist_loader
# def check_if_token_in_blacklist(decrypted_token):
#     jti = decrypted_token["jti"]
#     return jti in jwt_blocklist
