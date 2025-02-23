import os

import requests
from shortuuid import uuid

from flask import Blueprint, request

from app.api.helper import send_result, send_error, CONFIG

api = Blueprint('momo', __name__)

PARTNER_CODE = "MOMOBKUN20180529"
ACCESS_KEY = "F8BBA842ECF85"
SECRET_KEY = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
API_URL = "https://test-payment.momo.vn/v2/gateway/api/create"


import hmac
import hashlib

def generate_signature(data, secret_key):
    raw_data = "&".join(f"{k}={v}" for k, v in sorted(data.items()))
    signature = hmac.new(
        secret_key.encode('utf-8'),
        raw_data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature

@api.route("/create_payment", methods=['POST'])
def create_payment():
    try:
        order_id = f"order_{str(uuid())}"
        request_id = f"req_{str(uuid())}"

        payload = {
            "partnerCode": PARTNER_CODE,
            "accessKey": ACCESS_KEY,
            "requestId": request_id,
            "amount": "10000",
            "orderId": order_id,
            "orderInfo": "Thanh toán đơn hàng",
            "returnUrl": f"{CONFIG.BASE_URL_WEBSITE}/api/v1/momo/payment_return",
            "ipnUrl": f"{CONFIG.BASE_URL_WEBSITE}/api/v1/momo/payment_notify",
            "requestType": "captureWallet",
            "extraData": "",
        }

        # Tạo chữ ký
        payload["signature"] = generate_signature(payload, SECRET_KEY)

        # Gửi yêu cầu tới Momo
        response = requests.post(API_URL, json=payload)


        momo_response = response.json()

        print(momo_response)


        return send_result(data={
            "payUrl": momo_response.get("payUrl"),
            "errorCode": momo_response.get("errorCode"),
            "message": momo_response.get("message"),
        })

    except Exception as ex:
        return send_error(message=str(ex))


@api.route('/payment_return', methods=['GET'])
def payment_return():
    response_data = request.args.to_dict()
    return send_result(data=response_data)

# API xử lý thông báo thanh toán từ Momo (dành cho backend)
@api.route('/payment_notify', methods=['POST'])
def payment_notify():
    data = request.json
    return send_result(data=data)