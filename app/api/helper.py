import datetime
import os
import pickle
from typing import List
from flask import jsonify, request
from flask_jwt_extended import decode_token, get_jwt_identity, verify_jwt_in_request_optional
from flask_mail import Message as MessageMail
from jinja2 import Template

from app.extensions import logger, mail, red, db, mongo_db
from app.models import User, GroupRole, RolePermission, Message, Role
from app.settings import DevConfig
from app.utils import get_timestamp_now, no_accent_vietnamese

CONFIG = DevConfig


def get_permissions(user: User):
    """
    get all permission of user login
    Args:
        user:

    Returns:
        permissions:
    """
    permissions = []
    group_id = user.group_id
    list_role = GroupRole.query.filter(GroupRole.group_id == group_id).all()
    for group_role in list_role:
        list_permission = RolePermission.query.filter(RolePermission.role_id == group_role.role_id).all()
        for role_permission in list_permission:
            if role_permission.permission.resource not in permissions:
                permissions.append(role_permission.permission.resource)

    return permissions


def get_roles_key(user: User) -> List[Role]:
    """
    get all roles of user login
    Args:
        user:

    Returns:
        roles:
    """
    roles_key = []
    group_id = user.group_id
    list_role = GroupRole.query.filter(GroupRole.group_id == group_id).all()
    for group_role in list_role:
        role = Role.query.filter(Role.id == group_role.role_id).first()
        if role.key not in roles_key:
            roles_key.append(role.key)

    return roles_key


def get_user_id_request():
    user_id = None
    try:
        verify_jwt_in_request_optional()  # Không bắt buộc token
        user_id = get_jwt_identity()
    except Exception:
        pass
    return user_id

def send_result(data: any = None, message_id: str = '', message: str = "OK", code: int = 200,
                status: str = 'success', show: bool = False, duration: int = 0,
                val_error: dict = {}, is_dynamic: bool = False):
    """
    Args:
        data: simple result object like dict, string or list
        message: message send to client, default = OK
        code: code default = 200
        version: version of api
    :param data:
    :param message_id:
    :param message:
    :param code:
    :param status:
    :param show:
    :param duration:
    :return:
    json rendered sting result
    """
    message_dict = {
        "id": message_id,
        "text": message,
        "status": status,
        "show": show,
        "duration": duration,
        "dynamic": is_dynamic
    }
    message_obj: Message = Message.query.get(message_id)
    if message_obj:
        if message_dict['dynamic'] == 0:
            message_dict['text'] = message_obj.message
        else:
            if not message == 'OK':
                message_dict['text'] = message
            else:
                message_dict['text'] = message_obj.message.format(**val_error)
        message_dict['status'] = message_obj.status
        message_dict['show'] = message_obj.show
        message_dict['duration'] = message_obj.duration

    res = {
        "code": code,
        "data": data,
        "message": message_dict,
        "version": get_version(CONFIG.VERSION)
    }

    return jsonify(res), 200


def send_error(data: any = None, message_id: str = '', message: str = "Error", code: int = 400,
               status: str = 'error', show: bool = False, duration: int = 0,
               val_error: dict = {}, is_dynamic: bool = False):
    """

    :param data:
    :param message_id:
    :param message:
    :param code:
    :param status:
    :param show:
    :param duration:
    :return:
    """
    message_dict = {
        "id": message_id,
        "text": message,
        "status": status,
        "show": show,
        "duration": duration,
        "dynamic": is_dynamic
    }
    message_obj = Message.query.get(message_id)
    if message_obj:
        if message_dict['dynamic'] == 0:
            message_dict['text'] = message_obj.message
        else:
            if not message == 'Error':
                message_dict['text'] = message
            else:
                message_dict['text'] = message_obj.message.format(**val_error)

        message_dict['status'] = message_obj.status
        message_dict['show'] = message_obj.show
        message_dict['duration'] = message_obj.duration

    res = {
        "code": code,
        "data": data,
        "message": message_dict,
        "version": get_version(CONFIG.VERSION)
    }

    return jsonify(res), code


def get_version(version: str) -> str:
    """
    if version = 1, return api v1
    version = 2, return api v2
    Returns:

    """
    version_text = f"FIT APIs v{version}"
    return version_text


def send_email(recipient: str, title: str, body: str) -> None:
    """
    send email with flask mail
    :param recipient:
    :param title:
    :param body:
    :return:
    """
    msg = MessageMail(title, recipients=[recipient])
    msg.html = body
    # Try to send the email.
    try:
        mail.send(msg)
    except Exception as e:
        logger.error(str(e))
    else:
        logger.info('Successful mailing')


# The old function using smtp gmail
def send_email_template_old(recipient: str, title: str, template: str, data_fill: object):
    """
    send email with by template
    :param recipient:
    :param title:
    :param template:
    :param data_fill:
    :return: bool
    """
    try:
        template = Template(template)
        body = template.render(data_fill)  # fill data for template html
        send_email(recipient, title, body)  # send email
    except Exception as e:
        print(e.__str__())


def convert_birth_to_timestamp(date_of_birth: str):
    """
    send email with by template
    :param date_of_birth:
    :return: int
    """
    try:
        import time
        import datetime
        from pytz import timezone
        try:
            date = datetime.datetime.strptime(date_of_birth, "%d/%m/%Y %H:%M:%S")
        except:
            date = datetime.datetime.strptime(date_of_birth, "%Y-%m-%d %H:%M:%S")
        # convert string to timestamp with timezone saigon
        timezone_sg = timezone(CONFIG.TIME_ZONE)
        with_timezone = timezone_sg.localize(date)
        timestamp = int(with_timezone.timestamp())

        return timestamp
    except Exception as e:
        logger.error(e.__str__())
        return 0

def convert_to_datetime(date_str):
    try:
        # Chuyển chuỗi thành datetime với định dạng "dd/MM/yyyy"
        return datetime.datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        # Trả về None nếu định dạng không đúng
        return None

class Token:
    @classmethod
    def add_token_to_database(cls, encoded_token: str, user_id: str):
        decoded_token = decode_token(encoded_token)
        jti = decoded_token['jti']
        expires = int(decoded_token['exp'] - get_timestamp_now())

        tokens_jti = red.get(user_id)
        tokens_jti = tokens_jti.decode() + ',' + jti if tokens_jti else jti
        red.set(user_id, tokens_jti)
        red.set(jti, encoded_token, expires)

    @classmethod
    def revoke_token(cls, jti):
        red.delete(jti)

    @classmethod
    def is_token_revoked(cls, decoded_token):
        """
        Checks if the given token is revoked or not. Because we are adding all the
        token that we create into this database, if the token is not present
        in the database we are going to consider it revoked, as we don't know where
        it was created.
        """
        jti = decoded_token['jti']
        is_revoked = False
        if red.get(jti) is None:
            is_revoked = True
        return is_revoked

    @classmethod
    def revoke_all_token(cls, user_id: str):
        tokens_jti = red.get(user_id)
        tokens_jti = tokens_jti.decode() if tokens_jti else ''
        tokens_jti = tokens_jti.split(',')
        for jti in tokens_jti:
            red.delete(jti)
        red.set(user_id, '')

    @classmethod
    def add_list_permission(cls, user_id: str, list_permission: List[str]):
        permission_user = f"permission_{user_id}"
        red.set(permission_user, pickle.dumps(list_permission))




def send_email_template(recipient: str, title: str, template: str, data_fill: object, cc_recipient: str = ''):
    """
    send email with by template
    :param recipient:
    :param cc_recipient:
    :param title:
    :param template:
    :param data_fill:
    :return: bool
    """
    try:
        template = Template(template)
        body = template.render(data_fill)  # fill data for template html
        # send_email_aws(recipient=recipient, title=title, body=body)  # send email
        send_email(recipient=recipient, title=title, body=body)
        return True
    except Exception as e:
        print(e.__str__())

    return False


def render_template(template, data):
    try:
        template = Template(template)
        return template.render(data)
    except Exception as e:
        print(e.__str__())
    return False


def paginator_mongodb(query, page, page_size, total):
    """ handle paginator mongodb

    :param query:
    :param page:
    :param page_size:
    :param total:
    :return: bool
    """
    if page <= 0:
        return False, None, None
    if page_size <= 0:
        return False, None, None
    items = query.skip((page - 1) * page_size).limit(page_size)
    total_pages = total / page_size
    if total % page_size != 0:
        total_pages = total_pages + 1
    return True, items, total, int(total_pages)


def validate_str_notin_ascii(string: str):
    en_string = no_accent_vietnamese(string)
    if en_string.isascii():
        return True
    return False