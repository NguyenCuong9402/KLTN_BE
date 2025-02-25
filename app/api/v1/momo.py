import os
from shortuuid import uuid

from flask import Blueprint, request
from app.api.helper import send_result, send_error, CONFIG
import json
import requests
import hmac
import hashlib

from app.enums import TYPE_PAYMENT_ONLINE
from app.extensions import db
from app.models import PaymentOnline

api = Blueprint('momo', __name__)


MOMO_CONFIG = {
    "momo_api_create_payment": "https://test-payment.momo.vn/v2/gateway/api/create",
    "momo_api_check_payment": "https://test-payment.momo.vn/v2/gateway/api/query",
    "redirectUrl": "about:blank",
    "accessKey": "F8BBA842ECF85",
    "secretKey": "K951B6PE1waDMi640xX08PD3vg6EkVlz",
    "partnerCode": "MOMO",
    "partnerName" : "MoMo Payment",
    "requestType": "payWithMethod",
    "extraData": "",
    "autoCapture": True,
    "lang": "vi",
    "storeId": "Test Store",
    "orderGroupId": ""
}


STATUS_PAYMENT_MOMO_SUCCESS = 0

@api.route("/create_payment", methods=['POST'])
def create_payment():
    try:
        amount = 5000
        orderId = str(uuid())
        requestId = str(uuid())
        payment_online_id = str(uuid())
        ipnUrl = f"{CONFIG.BASE_URL_WEBSITE}/api/v1/momo/{TYPE_PAYMENT_ONLINE.get("momo")}/{payment_online_id}/payment_notify"
        orderInfo = "pay with MoMo"
        # Trang momo đt chuyển đến link web mình muốn
        # redirectUrl = f"https://www.facebook.com/"
        # Trang momo đt không làm gì sau khi thanh toán

        
        rawSignature = "accessKey=" + MOMO_CONFIG.get("accessKey") + "&amount=" + str(amount) + "&extraData=" + MOMO_CONFIG.get("extraData") + "&ipnUrl=" + ipnUrl + "&orderId=" + orderId \
                       + "&orderInfo=" + orderInfo + "&partnerCode=" + MOMO_CONFIG.get("partnerCode")+ "&redirectUrl=" + MOMO_CONFIG.get("redirectUrl") \
                       + "&requestId=" + requestId + "&requestType=" + MOMO_CONFIG.get("requestType")

        h = hmac.new(bytes(MOMO_CONFIG.get("secretKey"), 'ascii'), bytes(rawSignature, 'ascii'), hashlib.sha256)
        signature = h.hexdigest()

        payment_momo = PaymentOnline(id=payment_online_id,
                                     type=TYPE_PAYMENT_ONLINE.get('MOMO', 'momo'),
                                     order_payment_id=orderId, request_payment_id=requestId)
        db.session.add(payment_momo)
        db.session.flush()
        db.session.commit()

        data = {
            'partnerCode': MOMO_CONFIG.get("partnerCode"),
            'partnerName': MOMO_CONFIG.get("partnerName"),
            'storeId': MOMO_CONFIG.get("storeId"),
            'extraData': MOMO_CONFIG.get("extraData"),
            'orderGroupId': MOMO_CONFIG.get("orderGroupId"),
            'lang': MOMO_CONFIG.get("lang"),
            'requestType': MOMO_CONFIG.get("requestType"),
            'redirectUrl': MOMO_CONFIG.get("redirectUrl"),
            'autoCapture': MOMO_CONFIG.get("autoCapture"),
            'orderId': orderId,
            'orderInfo': orderInfo,
            'requestId': requestId,
            'ipnUrl': ipnUrl,
            'amount': str(amount),
            'signature': signature
        }

        data = json.dumps(data)

        clen = len(data)
        response = requests.post(MOMO_CONFIG.get("momo_api_create_payment"), data=data,
                                 headers={'Content-Type': 'application/json', 'Content-Length': str(clen)})
        # Trả về phản hồi
        data = response.json()
        return send_result(data=data)
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))

@api.route("<payment_momo_id>", methods=['GET'])
def check_payment(payment_momo_id):
    try:
        payment_momo = PaymentOnline.query.filter_by(id=payment_momo_id).first()

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
                if data.get('resultCode', None) == STATUS_PAYMENT_MOMO_SUCCESS:
                    payment_momo.status_payment = True

                db.session.flush()
                db.session.commit()
            else:
                if isinstance(payment_momo.result_payment, dict):
                    current_result_code = payment_momo.result_payment.get('resultCode', None)
                    if current_result_code != STATUS_PAYMENT_MOMO_SUCCESS and data.get('resultCode', None) == STATUS_PAYMENT_MOMO_SUCCESS:
                        payment_momo.result_payment = data
                        payment_momo.status_payment = True
                        db.session.flush()
                        db.session.commit()


        return send_result(message=data)

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))

# API xử lý thông báo thanh toán từ Momo (dành cho backend)
@api.route('/<type_payment>/<payment_online_id>/payment_notify', methods=['POST'])
def payment_notify(type_payment, payment_online_id):
    try:
        data = request.get_json()
        print("đã vào BE", data)
        payment_momo = PaymentOnline.query.filter(PaymentOnline.id == payment_online_id, type=type_payment ).first()
        if payment_momo is None:
            return send_error(message='Không tìm thấy giao dịch.')
        if isinstance(data, dict):
            payment_momo.result_payment = data
            if data.get('resultCode', None) == STATUS_PAYMENT_MOMO_SUCCESS:
                payment_momo.status_payment = True
        db.session.flush()
        db.session.commit()

        return send_result(data=data)

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))