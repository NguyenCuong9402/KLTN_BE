import copy
import datetime
import json
import random
import re
import string
import urllib.parse
from time import strftime
from flask import request
from marshmallow import fields, validate as validate_
from pytz import timezone
from .enums import TIME_FORMAT_LOG, ALLOWED_EXTENSIONS_IMG
from .extensions import logger


class FieldString(fields.String):
    """
    validate string field, max length = 1024
    Args:
        des:

    Returns:

    """
    DEFAULT_MAX_LENGTH = 1024  # 1 kB

    def __init__(self, validate=None, requirement=None, **metadata):
        """

        Args:
            validate:
            metadata:
        """
        if validate is None:
            validate = validate_.Length(max=self.DEFAULT_MAX_LENGTH)
        if requirement is not None:
            validate = validate_.NoneOf(error='Invalid input!', iterable={'full_name'})
        super(FieldString, self).__init__(validate=validate, required=requirement, **metadata)


class FieldNumber(fields.Number):
    """
    validate number field, max length = 30
    Args:
        des:

    Returns:

    """
    DEFAULT_MAX_LENGTH = 30  # 1 kB

    def __init__(self, validate=None, **metadata):
        """

        Args:
            validate:
            metadata:
        """
        if validate is None:
            validate = validate_.Length(max=self.DEFAULT_MAX_LENGTH)
        super(FieldNumber, self).__init__(validate=validate, **metadata)


def logged_input(json_req: str) -> None:
    """
    Logged input fields
    :param json_req:
    :return:
    """

    logger.info('%s %s %s %s %s INPUT FIELDS: %s',
                strftime(TIME_FORMAT_LOG),
                request.remote_addr,
                request.method,
                request.scheme,
                request.full_path,
                json_req)


def logged_error(error: str) -> None:
    """
    Logged input fields
    :param error:
    :return:
    """

    logger.info('%s %s %s %s %s ERROR: %s',
                strftime(TIME_FORMAT_LOG),
                request.remote_addr,
                request.method,
                request.scheme,
                request.full_path,
                error)

def allowed_file(filename: str) -> bool:
    """

    Args:
        filename:

    Returns:

    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMG


def get_datetime_now() -> datetime:
    """
        Returns:
            current datetime
    """
    time_zon_sg = timezone('Asia/Ho_Chi_Minh')
    return datetime.datetime.now(time_zon_sg)

def default_birthday():
    return date.today().replace(year=date.today().year - 18)

def get_datetime_now_utc() -> datetime:
    return datetime.datetime.now()


def get_timestamp_now() -> int:
    """
        Returns:
            current time in timestamp
    """
    time_zon_sg = timezone('Asia/Ho_Chi_Minh')
    return int(datetime.datetime.now(time_zon_sg).timestamp())


def get_timestamp_begin_today() -> int:
    """
        Returns:
            current time in timestamp
    """
    return get_timestamp_now() - get_timestamp_now() % 86400 - 7 * 3600


def dt_from_config_time_zone(timestamp):
    time_zone = timezone('Asia/Ho_Chi_Minh')
    return datetime.datetime.fromtimestamp(timestamp, tz=time_zone)


def is_contain_space(password: str) -> bool:
    """

    Args:
        password:

    Returns:
        True if password contain space
        False if password not contain space

    """
    return ' ' in password


def allowed_file_img(filename):
    """

    Args:
        filename:

    Returns:

    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMG


def get_another_phone(phone: str):
    """

    Args:
        phone:

    Returns:

    """
    if phone[0] == '+':
        return '0' + phone[3:]
    return '+84' + phone[1:]


def trim_dict(input_dict: dict) -> dict:
    """

    Args:
        input_dict:

    Returns:

    """
    # trim dict
    new_dict = {}
    for key, value in input_dict.items():
        if isinstance(value, str):
            new_dict[key] = value.strip()
        else:
            new_dict[key] = value
    return new_dict


def data_preprocessing(cls_validator, input_json: dict):
    """
    Data preprocessing trim then check validate
    :param cls_validator:
    :param input_json:
    :return: status of class validate
    """
    for key, value in input_json.items():
        if isinstance(value, str):
            input_json[key] = value.strip()
    return cls_validator().custom_validate(input_json)


def divide_chunks(list_obj: list, page_size: int) -> list:
    """
    custom sort
    :param list_obj: list object
    :param page_size: page size
    :return: list object
    """
    for i in range(0, len(list_obj), page_size):
        yield list_obj[i:i + page_size]


def generate_password():
    """
    :return: random password
    """
    symbol_list = ["@", "$", "!", "%", "*", "?", "&"]
    number = '0123456789'
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join(random.choices(letters_and_digits, k=6))
    return '{}{}{}'.format(result_str, random.choice(symbol_list), random.choice(number))


def decode_redis_message(redis_byte_obj):
    """

    :param redis_byte_obj:
    :return:
    """
    return_data = json.loads(redis_byte_obj.decode()) if type(redis_byte_obj) == bytes else None
    return return_data


def escape_wildcard(search):
    """
    :param search:
    :return:
    """
    search1 = str.replace(search, '\\', r'\\')
    search2 = str.replace(search1, r'%', r'\%')
    search3 = str.replace(search2, r'_', r'\_')
    search4 = str.replace(search3, r'[', r'\[')
    search5 = str.replace(search4, r'"', r'\"')
    search6 = str.replace(search5, r"'", r"\'")
    return search6


def escape_wildcard_mongodb(search):
    """
    :param search:
    :return:
    """
    special_chars = r'[-/\\^$*+?.()|[\]{}]'
    escaped_str = re.sub(special_chars, r'\\\g<0>', search)
    return escaped_str


def no_accent_vietnamese(s):
    """
        Function convert string vietnamese
        Returns: string not mark
        Examples::
    """
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(r'[ÀÁẠẢÃĂẰẮẶẲẴÂẦẤẬẨẪ]', 'A', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
    s = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
    s = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s)
    s = re.sub(r'[ÌÍỊỈĨ]', 'I', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
    s = re.sub(r'[ƯỪỨỰỬỮÙÚỤỦŨ]', 'U', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
    s = re.sub(r'[ỲÝỴỶỸ]', 'Y', s)
    s = re.sub(r'[Đ]', 'D', s)
    s = re.sub(r'[đ]', 'd', s)
    return s


def normalize_search_input(search_name: str, db='mysql'):
    """ normalize input string in utf-8

    Args:
        search_name: string

    Returns:

    """
    search_name = urllib.parse.unquote(search_name, encoding='utf-8', errors='replace') if search_name else None
    if search_name:
        search_name = search_name.strip()
        if db == 'mongodb':
            search_name = escape_wildcard_mongodb(search_name)
        else:
            search_name = escape_wildcard(search_name)
    return search_name

def is_contained_accent_vietnamese(s: str) -> bool:
    """

    :param s:
    :return:
    """
    accent_vietnamese = ['à', 'á', 'ạ', 'ả', 'ã', 'â', 'ầ', 'ấ', 'ậ', 'ẩ', 'ẫ', 'ă', 'ằ', 'ắ', 'ặ', 'ẳ', 'ẵ', 'À', 'Á',
                         'Ạ', 'Ả', 'Ã', 'Ă', 'Ằ', 'Ắ', 'Ặ', 'Ẳ', 'Ẵ', 'Â', 'Ầ', 'Ấ', 'Ậ', 'Ẩ', 'Ẫ', 'è', 'é', 'ẹ', 'ẻ',
                         'ẽ', 'ê', 'ề', 'ế', 'ệ', 'ể', 'ễ', 'È', 'É', 'Ẹ', 'Ẻ', 'Ẽ', 'Ê', 'Ề', 'Ế', 'Ệ', 'Ể', 'Ễ', 'ò',
                         'ó', 'ọ', 'ỏ', 'õ', 'ô', 'ồ', 'ố', 'ộ', 'ổ', 'ỗ', 'ơ', 'ờ', 'ớ', 'ợ', 'ở', 'ỡ', 'Ò', 'Ó', 'Ọ',
                         'Ỏ', 'Õ', 'Ô', 'Ồ', 'Ố', 'Ộ', 'Ổ', 'Ỗ', 'Ơ', 'Ờ', 'Ớ', 'Ợ', 'Ở', 'Ỡ', 'ì', 'í', 'ị', 'ỉ', 'ĩ',
                         'Ì', 'Í', 'Ị', 'Ỉ', 'Ĩ', 'ù', 'ú', 'ụ', 'ủ', 'ũ', 'ư', 'ừ', 'ứ', 'ự', 'ử', 'ữ', 'Ư', 'Ừ', 'Ứ',
                         'Ự', 'Ử', 'Ữ', 'Ù', 'Ú', 'Ụ', 'Ủ', 'Ũ', 'ỳ', 'ý', 'ỵ', 'ỷ', 'ỹ', 'Ỳ', 'Ý', 'Ỵ', 'Ỷ', 'Ỹ', 'Đ',
                         'đ']
    for accent in accent_vietnamese:
        if accent in s:
            return True
    return False


def my_read_excel(df, mapping_keys: dict):
    instance = []
    for i in range(len(df)):
        tmp_instance = {}
        for key, new_key in mapping_keys.items():
            item_value = df[key][i] if str(df[key][i]) not in ['nan', ''] else None
            if type(item_value) is str:
                words = copy.copy(item_value).split()
                item_value = ' '.join(words)
            tmp_instance.setdefault(new_key, item_value)
        instance.append(tmp_instance)
    return instance


def generate_random_number_string():
    return ''.join([str(random.randint(0, 9)) for _ in range(4)])


def body_mail(mail_id, replacements):
    from .models import EmailTemplate
    try:
        mail = EmailTemplate.query.filter(EmailTemplate.id==mail_id).first()
        text = mail.body
        for key, value in replacements.items():
            placeholder = f'$"{key}"'
            text = text.replace(placeholder, str(value))
        return text
    except Exception as ex:
        print(str(ex))

# Regex validate
RE_ONLY_NUMBERS = r'^(\d+)$'
RE_ONLY_CHARACTERS = r'^[a-zA-Z]+$'
RE_ONLY_NUMBER_AND_DASH = r'^[-\d]+$'
RE_ONLY_LETTERS_NUMBERS_PLUS = r'^[+A-Za-z0-9]+$'
REGEX_EMAIL = r'^(([^<>()[\]\.,;:\s@\"]+(\.[^<>()[\]\.,;:\s@\"]+)*)|(\".+\"))@(([^<>()[\]\.,;:\s@\"]+\.)+[^<>()[\]\.,' \
              r';:\s@\"]{2,})$'
REGEX_PHONE_NUMBER = r'^\+?[1-9]|^[0-9]{0,20}$'
REGEX_OTP = r'[0-9]{6}'
REGEX_FULLNAME_VIETNAMESE = r"([^0-9`~!@#$%^&*(),.?'\":;{}+=|<>_\-\\\/\[\]]+)$"
REGEX_URL = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<" \
            r">]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

REGEX_ADDRESS_VIETNAMESE = r"([^`~!@#$%^&*().?'\":;{}+=|<>_\-\\\[\]]+)$"
REGEX_VALID_PASSWORD = r'^(?=.*[0-9])(?=.*[a-zA-Z])(?!.* ).{8,16}$'
secret_key_serpapi = "13b70e23408306d0e6f4b1f7e59b6fc3643128c415e9696a6502102d5166cf59"
