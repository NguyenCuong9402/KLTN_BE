from shortuuid import uuid
from flask import Blueprint, request
from app.api.helper import send_result, send_error, CONFIG
from app.enums import TYPE_PAYMENT_ONLINE, MOMO_CONFIG, ZALO_CONFIG

from app.extensions import db
from time import time
from datetime import datetime
import json, hmac, hashlib
import requests

from app.models import PaymentOnline
from app.utils import get_timestamp_now

api = Blueprint('payment_online', __name__)


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
                if data.get('resultCode', None) == MOMO_CONFIG.get("status_success"):
                    payment_online.status_payment = True

            db.session.flush()
            db.session.commit()

        return send_result(data=data)
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))



@api.route("/momo/<payment_id>", methods=['GET'])
def check_payment(payment_id):
    try:
        payment_momo = PaymentOnline.query.filter_by(id=payment_id, type=TYPE_PAYMENT_ONLINE.get("MOMO", "momo")).first()

        if payment_momo is None:
            return send_error(message="Không tìm thấy giao dịch.")

        rawSignature = ("accessKey=" + MOMO_CONFIG.get("accessKey") + "&orderId=" + payment_momo.order_payment_id + "&partnerCode=" + MOMO_CONFIG.get("partnerCode") +
                        "&requestId=" + payment_momo.request_payment_id)


        h = hmac.new(bytes(MOMO_CONFIG.get("secretKey"), 'ascii'), bytes(rawSignature, 'ascii'), hashlib.sha256)
        signature = h.hexdigest()

        data = {
            'partnerCode': MOMO_CONFIG.get("partnerCode"),
            'orderId': payment_momo.order_payment_id,
            'requestId': payment_momo.request_payment_id,
            'signature': signature,
            'lang': MOMO_CONFIG.get("lang"),
        }
        response = requests.post(MOMO_CONFIG.get("momo_api_check_payment"), json=data, headers={'Content-Type': 'application/json'})
        data = response.json()

        if isinstance(data, dict):
            if payment_momo.result_payment is None:
                payment_momo.result_payment = data
                if data.get('resultCode', None) == MOMO_CONFIG.get("status_success"):
                    payment_momo.status_payment = True

                db.session.flush()
                db.session.commit()
            else:
                if isinstance(payment_momo.result_payment, dict):
                    current_result_code = payment_momo.result_payment.get('resultCode', None)
                    if current_result_code != MOMO_CONFIG.get("status_success") and data.get('resultCode', None) == MOMO_CONFIG.get("status_success"):
                        payment_momo.result_payment = data
                        payment_momo.status_payment = True
                        db.session.flush()
                        db.session.commit()

        return send_result(message=data)

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))