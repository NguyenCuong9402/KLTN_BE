from shortuuid import uuid

from flask import Blueprint, request
from app.api.helper import send_result, send_error, CONFIG
import json
import requests
import hmac
import hashlib

from app.api.v1.zalo import ZALO_CONFIG
from app.enums import TYPE_PAYMENT_ONLINE, MOMO_CONFIG
from app.extensions import db
from app.models import PaymentOnline

api = Blueprint('momo', __name__)

@api.route("/create_payment", methods=['POST'])
def create_payment():
    try:
        amount = 5000
        orderId = str(uuid())
        requestId = str(uuid())
        payment_online_id = str(uuid())
        ipnUrl = f"{CONFIG.BASE_URL_WEBSITE}/api/v1/payment_online/{TYPE_PAYMENT_ONLINE.get("MOMO", "momo")}/{payment_online_id}/payment_notify"
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

        data_result = {
            'result': data,
        }
        if data.get("payUrl", None) and data.get("resultCode", None) == 0:
            data_result['pay_url'] = data.get("payUrl")

        return send_result(data=data_result)
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))