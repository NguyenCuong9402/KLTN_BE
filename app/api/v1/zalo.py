import os
from shortuuid import uuid

from flask import Blueprint, request
from app.api.helper import send_result, send_error, CONFIG

from app.extensions import db
from time import time
from datetime import datetime
import json, hmac, hashlib, urllib.request, urllib.parse

api = Blueprint('zalo', __name__)

zalo_api_create_payment = "https://sb-openapi.zalopay.vn/v2/create"

config = {
  "app_id": 2553,
  "key1": "PcY4iZIKFCIdgZvA6ueMcMHHUbRLYjPL",
  "key2": "kLtgPl8HHhfvMuDHPwKfgfsY4Ydm9eIz",
  "endpoint": "https://sb-openapi.zalopay.vn/v2/create"
}

embed_data = "{}"
item = "[]",

STATUS_PAYMENT_MOMO_SUCCESS = 0

@api.route("/create_payment", methods=['POST'])
def create_payment():
    try:
        amount = 10000
        orderId = str(uuid())
        requestId = str(uuid())

        transID = f"{orderId}-{requestId}"

        order = {
            "app_id": config["app_id"],
            "app_trans_id": "{:%y%m%d}_{}".format(datetime.today(), transID),  # mã giao dich có định dạng yyMMdd_xxxx
            "app_user": "user123",
            "app_time": int(round(time() * 1000)),  # miliseconds
            "embed_data": json.dumps({}),
            "item": json.dumps([{}]),
            "amount": amount,
            "description": "Lazada - Payment for the order #" + str(transID),
            "bank_code": "zalopayapp"
        }

        data = "{}|{}|{}|{}|{}|{}|{}".format(order["app_id"], order["app_trans_id"], order["app_user"],
                                             order["amount"], order["app_time"], order["embed_data"], order["item"])

        order["mac"] = hmac.new(config['key1'].encode(), data.encode(), hashlib.sha256).hexdigest()

        response = urllib.request.urlopen(url=config["endpoint"], data=urllib.parse.urlencode(order).encode())
        result = json.loads(response.read())

        return send_result(data=result)
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))

# @api.route("<payment_momo_id>", methods=['GET'])
# def check_payment(payment_momo_id):
#     try:
#         payment_momo = PaymentMomo.query.filter_by(id=payment_momo_id).first()
#
#         if payment_momo is None:
#             return send_error(message="Không tìm thấy giao dịch.")
#
#         rawSignature = ("accessKey=" + accessKey + "&orderId=" + payment_momo.order_momo_id + "&partnerCode=" + partnerCode +
#                         "&requestId=" + payment_momo.request_momo_id)
#
#
#         h = hmac.new(bytes(secretKey, 'ascii'), bytes(rawSignature, 'ascii'), hashlib.sha256)
#         signature = h.hexdigest()
#
#         data = {
#             'partnerCode': partnerCode,
#             'orderId': payment_momo.order_momo_id,
#             'requestId': payment_momo.request_momo_id,
#             'signature': signature,
#             'lang': lang,
#
#         }
#
#         response = requests.post(momo_api_check_payment, json=data, headers={'Content-Type': 'application/json'})
#
#
#         data = response.json()
#
#         if isinstance(data, dict):
#             if payment_momo.result_momo is None:
#                 payment_momo.result_momo = data
#                 if data.get('resultCode', None) == STATUS_PAYMENT_MOMO_SUCCESS:
#                     payment_momo.status_payment = True
#
#                 db.session.flush()
#                 db.session.commit()
#             else:
#                 if isinstance(payment_momo.result_momo, dict):
#                     current_result_code = payment_momo.result_momo.get('resultCode', None)
#                     if current_result_code != STATUS_PAYMENT_MOMO_SUCCESS and data.get('resultCode', None) == STATUS_PAYMENT_MOMO_SUCCESS:
#                         payment_momo.result_momo = data
#                         payment_momo.status_payment = True
#                         db.session.flush()
#                         db.session.commit()
#
#
#         return send_result(message=data)
#
#     except Exception as ex:
#         db.session.rollback()
#         return send_error(message=str(ex))
#
# @api.route('/<order_momo_id>/<request_momo_id>/payment_return', methods=['GET'])
# def payment_return(order_momo_id, request_momo_id):
#     try:
#         response_data = request.args.to_dict()
#         return send_result(data=response_data)
#
#     except Exception as ex:
#         db.session.rollback()
#         return send_error(message=str(ex))
#
# API xử lý thông báo thanh toán từ Momo (dành cho backend)
@api.route('/payment_notify', methods=['POST'])
def payment_notify():
    try:
        data = request.get_json()
        print("đã vào BE", data)
        # payment_momo = PaymentMomo.query.filter(PaymentMomo.order_momo_id == order_momo_id,
        #                                         PaymentMomo.request_momo_id == request_momo_id).first()
        #
        #
        # if payment_momo is None:
        #     return send_error(message='Không tìm thấy giao dịch.')
        # if isinstance(data, dict):
        #     payment_momo.result_momo = data
        #     if data.get('resultCode', None) == STATUS_PAYMENT_MOMO_SUCCESS:
        #         payment_momo.status_payment = True
        # db.session.flush()
        # db.session.commit()
        return send_result(data=data)

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))