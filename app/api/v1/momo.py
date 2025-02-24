import os
from shortuuid import uuid

from flask import Blueprint, request
from app.api.helper import send_result, send_error, CONFIG
import json
import requests
import hmac
import hashlib

api = Blueprint('momo', __name__)

endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"
accessKey = "F8BBA842ECF85"
secretKey = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
orderInfo = "pay with MoMo"
partnerCode = "MOMO"
partnerName = "MoMo Payment"
requestType = "payWithMethod"
extraData = ""  # pass empty value or Encode base64 JsonString
autoCapture = True
lang = "vi"
redirectUrl = f"{CONFIG.BASE_URL_WEBSITE}/api/v1/momo/payment_return"
ipnUrl = f"{CONFIG.BASE_URL_WEBSITE}/api/v1/momo/payment_notify"



@api.route("/create_payment", methods=['POST'])
def create_payment():
    try:

        amount = "60000"
        orderId = str(uuid())
        requestId = str(uuid())
        storeId = "Test Store"
        orderGroupId = ""
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
        response = requests.post(endpoint, data=data,
                                 headers={'Content-Type': 'application/json', 'Content-Length': str(clen)})
        # Trả về phản hồi
        data = response.json()

        return send_result(data=data)
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