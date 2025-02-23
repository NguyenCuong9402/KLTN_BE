import os
from shortuuid import uuid

from flask import Blueprint, request
import uuid
import requests
import hmac
import hashlib
from app.api.helper import send_result, send_error, CONFIG

api = Blueprint('momo', __name__)

MOMO_API_URL = "https://test-payment.momo.vn/v2/gateway/api/create"
ACCESS_KEY = "F8BBA842ECF85"
SECRET_KEY = "K951B6PE1waDMi640xX08PD3vg6EkVlz"


def generate_signature(secret_key, data):
    """Tạo chữ ký HMAC SHA256 cho MoMo theo thứ tự chính xác."""
    raw_signature = "&".join(f"{key}={value}" for key, value in sorted(data.items()) if value != "")
    return hmac.new(secret_key.encode(), raw_signature.encode(), hashlib.sha256).hexdigest()


@api.route("/create_payment", methods=['POST'])
def create_payment():
    try:
        # Tạo payload cho MoMo
        payload = {
            "partnerCode": "MOMO",
            "accessKey": ACCESS_KEY,
            "requestId": str(uuid.uuid4()),
            "amount": "50000",
            "orderId": str(uuid.uuid4()),
            "orderInfo": "Thanh toán MoMo",
            "redirectUrl": f"{CONFIG.BASE_URL_WEBSITE}/api/v1/momo/payment_return",
            "ipnUrl": f"{CONFIG.BASE_URL_WEBSITE}/api/v1/momo/payment_notify",
            "extraData": "",
            "requestType": "captureWallet",
            "autoCapture": True,
            "lang": "vi"
        }

        # Thêm chữ ký
        payload["signature"] = generate_signature(SECRET_KEY, payload)

        # Gửi request đến MoMo
        response = requests.post(MOMO_API_URL, json=payload, headers={"Content-Type": "application/json"})

        # Trả về phản hồi
        return send_result(data=response.json())
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