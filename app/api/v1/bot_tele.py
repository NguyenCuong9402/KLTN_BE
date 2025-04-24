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
from app.utils import trim_dict, escape_wildcard, get_timestamp_now
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

    print(data)
    if 'message' not in data:
        print("Không có message")

    message = data['message']['text']
    chat_id = data['message']['chat']['id']

    MESSAGE = "Chào bạn, tôi là bot. Còn bạn là top"

    url = f"https://api.telegram.org/bot{DevConfig.TOKEN_BOT_TELE}/sendMessage"
    payload = {"chat_id": chat_id, "text": MESSAGE}

    response = requests.post(url, json=payload)

    print("Done")

    return '', 200  # Phản hồi trống với mã trạng thái 200
