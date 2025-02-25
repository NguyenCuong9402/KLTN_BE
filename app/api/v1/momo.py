import os
from shortuuid import uuid

from flask import Blueprint, request
from app.api.helper import send_result, send_error, CONFIG
import json
import requests
import hmac
import hashlib

from app.extensions import db
from app.models import PaymentMomo

api = Blueprint('momo', __name__)

momo_api_create_payment = "https://test-payment.momo.vn/v2/gateway/api/create"
momo_api_check_payment = "https://test-payment.momo.vn/v2/gateway/api/query"
accessKey = "F8BBA842ECF85"
secretKey = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
partnerCode = "MOMO"
partnerName = "MoMo Payment"
requestType = "payWithMethod"
extraData = ""  # pass empty value or Encode base64 JsonString
autoCapture = True
lang = "vi"

storeId = "Test Store"
orderGroupId = ""


STATUS_PAYMENT_MOMO_SUCCESS = 0

@api.route("/create_payment", methods=['POST'])
def create_payment():
    try:

        amount = "60000"
        orderId = str(uuid())
        requestId = str(uuid())

        payment_momo = PaymentMomo(id=str(uuid()), order_momo_id=orderId, request_momo_id=requestId)
        db.session.add(payment_momo)
        db.session.flush()
        db.session.commit()

        redirectUrl = f"{CONFIG.BASE_URL_WEBSITE}/api/v1/momo/{orderId}/{requestId}/payment_return"
        ipnUrl = f"{CONFIG.BASE_URL_WEBSITE}/api/v1/momo/{orderId}/{requestId}/payment_notify"
        orderInfo = f"Thanh toán hóa đơn {orderId}"

        rawSignature = "accessKey=" + accessKey + "&amount=" + amount + "&extraData=" + extraData + "&ipnUrl=" + ipnUrl + "&orderId=" + orderId \
                       + "&orderInfo=" + orderInfo + "&partnerCode=" + partnerCode + "&redirectUrl=" + redirectUrl \
                       + "&requestId=" + requestId + "&requestType=" + requestType

        h = hmac.new(bytes(secretKey, 'ascii'), bytes(rawSignature, 'ascii'), hashlib.sha256)
        signature = h.hexdigest()
        data = {
            'partnerCode': partnerCode,
            'orderId': orderId,
            'partnerName': partnerName,
            'storeId': storeId,
            'ipnUrl': ipnUrl,
            'amount': amount,
            'lang': lang,
            'requestType': requestType,
            'redirectUrl': redirectUrl,
            'autoCapture': autoCapture,
            'orderInfo': orderInfo,
            'requestId': requestId,
            'extraData': extraData,
            'signature': signature,
            'orderGroupId': orderGroupId
        }

        data = json.dumps(data)

        clen = len(data)
        response = requests.post(momo_api_create_payment, data=data,
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
        payment_momo = PaymentMomo.query.filter_by(id=payment_momo_id).first()

        if payment_momo is None:
            return send_error(message="Không tìm thấy giao dịch.")

        rawSignature = ("accessKey=" + accessKey + "&orderId=" + payment_momo.order_momo_id + "&partnerCode=" + partnerCode +
                        "&requestId=" + payment_momo.request_momo_id)


        h = hmac.new(bytes(secretKey, 'ascii'), bytes(rawSignature, 'ascii'), hashlib.sha256)
        signature = h.hexdigest()

        data = {
            'partnerCode': partnerCode,
            'orderId': payment_momo.order_momo_id,
            'requestId': payment_momo.request_momo_id,
            'signature': signature,
            'lang': lang,

        }

        response = requests.post(momo_api_check_payment, json=data, headers={'Content-Type': 'application/json'})


        data = response.json()

        if isinstance(data, dict):
            if payment_momo.result_momo is None:
                payment_momo.result_momo = data
                if data.get('resultCode', None) == STATUS_PAYMENT_MOMO_SUCCESS:
                    payment_momo.status_payment = True

                db.session.flush()
                db.session.commit()
            else:
                if isinstance(payment_momo.result_momo, dict):
                    current_result_code = payment_momo.result_momo.get('resultCode', None)
                    if current_result_code != STATUS_PAYMENT_MOMO_SUCCESS and data.get('resultCode', None) == STATUS_PAYMENT_MOMO_SUCCESS:
                        payment_momo.result_momo = data
                        payment_momo.status_payment = True
                        db.session.flush()
                        db.session.commit()


        return send_result(message=data)

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))

@api.route('/<order_momo_id>/<request_momo_id>/payment_return', methods=['GET'])
def payment_return(order_momo_id, request_momo_id):
    try:
        response_data = request.args.to_dict()
        return send_result(data=response_data)

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))

# API xử lý thông báo thanh toán từ Momo (dành cho backend)
@api.route('/<order_momo_id>/<request_momo_id>/payment_notify', methods=['POST'])
def payment_notify(order_momo_id, request_momo_id):
    try:
        data = request.get_json()
        print("đã vào BE", data)
        payment_momo = PaymentMomo.query.filter(PaymentMomo.order_momo_id == order_momo_id,
                                                PaymentMomo.request_momo_id == request_momo_id).first()


        if payment_momo is None:
            return send_error(message='Không tìm thấy giao dịch.')
        if isinstance(data, dict):
            payment_momo.result_momo = data
            if data.get('resultCode', None) == STATUS_PAYMENT_MOMO_SUCCESS:
                payment_momo.status_payment = True
        db.session.flush()
        db.session.commit()

        return send_result(data=data)

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))