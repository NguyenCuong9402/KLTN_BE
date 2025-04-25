import requests
from app.settings import DevConfig
from shortuuid import uuid
from flask import Blueprint, request
from sqlalchemy import desc, asc
from sqlalchemy.sql.visitors import replacement_traverse
from sqlalchemy_pagination import paginate

from app.enums import LAYER_COMMENT
from app.extensions import db
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request_optional
from app.api.helper import send_result, send_error, get_user_id_request
from app.models import User, Article, Community, Product, ArticleTagProduct, Comment
from app.signal import handle_article_notification
from app.utils import trim_dict, escape_wildcard, get_timestamp_now, command_dict, sendMessage
from app.validator import ProductValidation, ArticleSchema, QueryParamsAllSchema, ArticleValidate, \
    QueryParamsArticleSchema, CommentParamsValidation, CommentSchema

api = Blueprint('bot_tele', __name__)

# web hook -> Khi bật ngrok sẽ có cách nhận luôn tin nhắn.
# https://api.telegram.org/botTOKEN/setWebhook?url=YOUR_WEBHOOK_URL
# https://api.telegram.org/botTOKEN/getWebhookInfo
# https://api.telegram.org/botTOKEN/deleteWebhook

# Gửi ảnh
# https://api.telegram.org/botTOKEN/sendPhoto?chat_id=CHAT_ID&photo=IMAGE_URL


@api.route('', methods=['POST'])
def web_hook_tele():
    data = request.get_json()

    if 'message' not in data:
        print("Không có message")
        return 'Invalid message', 200

    message = data['message']['text']
    chat_id = data['message']['chat']['id']

    if not chat_id:
        return 'Invalid message', 200

    parts = message.strip().split(' ', 1)  # Tách theo khoảng trắng và giới hạn 2 phần

    if len(parts) == 2:  # Kiểm tra nếu có đúng 2 phần
        command = parts[0]  # Phần đầu tiên (lệnh)
        content = parts[1]  # Phần thứ 2 (nội dung nếu có)

        # Kiểm tra lệnh và gọi các function tương ứng
        func = command_dict.get(command)
        if func:
            func(chat_id, content)  # Gọi hàm tương ứng với lệnh
        else:
            MESSAGE = f"Lệnh không hợp lệ"
            sendMessage(chat_id, MESSAGE)
            return 'Invalid command', 200

    else:
        MESSAGE = f"Lệnh không hợp lệ"
        sendMessage(chat_id, MESSAGE)
        return 'Invalid message format', 200

    return 'OK', 200



