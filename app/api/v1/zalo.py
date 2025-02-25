import os
from shortuuid import uuid
from flask import Blueprint, request
from app.api.helper import send_result, send_error, CONFIG
from app.enums import TYPE_PAYMENT_ONLINE

from app.extensions import db
from time import time
from datetime import datetime
import json, hmac, hashlib
import requests

from app.models import PaymentOnline
from app.utils import get_timestamp_now

api = Blueprint('zalo', __name__)

APP_ID = 2553
APP_USER = "user123"
ZALO_CONFIG = {
    "key1": "PcY4iZIKFCIdgZvA6ueMcMHHUbRLYjPL",
    "key2": "kLtgPl8HHhfvMuDHPwKfgfsY4Ydm9eIz",
    "app_id":2553,
    "app_user": "user123",
    "bank_code": "zalopayapp",
    "endpoint_create_payment": "https://sb-openapi.zalopay.vn/v2/create",
    "status_success": 1
}

STATUS_PAYMENT_MOMO_SUCCESS = 0

@api.route("/create_payment", methods=['POST'])
def create_payment():
    try:
        amount = 10000
        order_id = str(uuid())
        request_id = "{:%y%m%d}_{}".format(datetime.today(), get_timestamp_now())
        order = {
            "app_id": ZALO_CONFIG.get("app_id"),
            "app_trans_id": request_id ,  # mã giao dich có định dạng yyMMdd_xxxx
            "app_user": ZALO_CONFIG.get("app_user"),
            "app_time": int(round(time() * 1000)),  # miliseconds
            "embed_data": json.dumps({}),
            "item": json.dumps([{}]),
            "amount": amount,
            "description": "Payment for the order #" + str(order_id),
            "bank_code": ZALO_CONFIG.get("bank_code"),
        }

        # app_id|app_trans_id|app_user|amount|apptime|embed_data|item
        raw_signature = "{}|{}|{}|{}|{}|{}|{}".format(order["app_id"], order["app_trans_id"], order["app_user"],
                                             order["amount"], order["app_time"], order["embed_data"], order["item"])

        # signature
        mac_signature = hmac.new(ZALO_CONFIG['key1'].encode(), raw_signature.encode(), hashlib.sha256).hexdigest()
        order["mac"] = mac_signature

        payment_zalo = PaymentOnline(id=str(uuid()), order_payment_id=order_id, request_payment_id=request_id,
                                     type=TYPE_PAYMENT_ONLINE.get('ZALO', 'zalo'),)

        # set link callback
        callback_url = f"{CONFIG.BASE_URL_WEBSITE}/api/v1/zalo/zalo/{payment_zalo.id}/payment_notify"
        order["callback_url"] = callback_url


        db.session.add(payment_zalo)
        db.session.flush()
        db.session.commit()

        response = requests.post(ZALO_CONFIG.get("endpoint_create_payment"), data=order)

        # Đọc kết quả JSON
        result = response.json()

        data_result = {
            'result': result,
        }

        if result.get("order_url", None) and result.get("return_code", None) == 1:
            data_result['pay_url'] = result.get("order_url")

        return send_result(data=data_result)
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))


# API xử lý thông báo thanh toán từ Momo (dành cho backend)
@api.route('/<type_payment>/<payment_online>/payment_notify', methods=['POST'])
def payment_notify(type_payment, payment_online):
    try:
        data = request.get_json()
        print("đã vào BE", data)
        payment_online = PaymentOnline.query.filter_by(id=payment_online, type=type_payment).first()
        if payment_online is None:
            return send_error(message='Không tìm thấy giao dịch.')
        if isinstance(data, dict):
            payment_online.result_payment = data
            if type_payment == TYPE_PAYMENT_ONLINE.get('ZALO', 'zalo'):
                if data.get('type', None) == ZALO_CONFIG.get("status_success"):
                    payment_online.status_payment = True

            elif type_payment == TYPE_PAYMENT_ONLINE.get('MOMO', 'momo'):
                if data.get('resultCode', None) == STATUS_PAYMENT_MOMO_SUCCESS:
                    payment_online.status_payment = True

            db.session.flush()
            db.session.commit()

        return send_result(data=data)
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))