from flask_jwt_extended import jwt_required, get_jwt_identity
from shortuuid import uuid
from flask import Blueprint, request
from app.api.helper import send_result, send_error, CONFIG
from app.enums import TYPE_PAYMENT_ONLINE, MOMO_CONFIG, ZALO_CONFIG, regions

from app.extensions import db
from time import time
from datetime import datetime
import json, hmac, hashlib
import requests

from app.gateway import authorization_require
from app.models import PaymentOnline, User, SessionOrder, Shipper, AddressOrder, PriceShip
from app.utils import get_timestamp_now, trim_dict
from app.validator import ProductValidation, PaymentValidation, PaymentOnlineSchema

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


@api.route("<payment_id>", methods=['GET'])
def check_payment(payment_id):
    try:
        payment_online = PaymentOnline.query.filter_by(id=payment_id).first()

        if payment_online is None:
            return send_error(message="Không tìm thấy giao dịch.")

        if payment_online.status_payment and payment_online.result_payment:
            return send_result(data=PaymentOnlineSchema().dump(payment_online), message="Giao dịch thành công")
        try:
            if payment_online.type == TYPE_PAYMENT_ONLINE.get('ZALO', 'zalo'):
                params = {
                    "app_id": ZALO_CONFIG.get("app_id"),
                    "app_trans_id": payment_online.request_payment_id  # Input your app_trans_id"
                }
                raw_signature = "{}|{}|{}".format(ZALO_CONFIG.get("app_id"), params["app_trans_id"], ZALO_CONFIG.get("key1"))
                mac_signature = hmac.new(ZALO_CONFIG['key1'].encode(), raw_signature.encode(), hashlib.sha256).hexdigest()
                params["mac"] = mac_signature

                response = requests.post(
                    ZALO_CONFIG["zalo_api_check_payment"],
                    json=params,
                    headers={'Content-Type': 'application/json'}
                )

                data = response.json()

                if isinstance(data, dict):
                    if payment_online.result_payment is None:
                        if data.get('return_code', None) == ZALO_CONFIG.get("status_success"):
                            payment_online.status_payment = True
                            data['type'] = ZALO_CONFIG.get("status_success")
                        else:
                            data['type'] = 0
                        payment_online.result_payment = data
                        db.session.flush()
                        db.session.commit()
                    else:
                        if isinstance(payment_online.result_payment, dict):
                            current_result_code = payment_online.result_payment.get('type', None)
                            if current_result_code != ZALO_CONFIG.get("status_success") and data.get('return_code', None) == ZALO_CONFIG.get("status_success"):
                                data['type'] = ZALO_CONFIG.get("status_success")
                                payment_online.result_payment = data
                                payment_online.status_payment = True
                                db.session.flush()
                                db.session.commit()
            else:
                rawSignature = ("accessKey=" + MOMO_CONFIG.get(
                    "accessKey") + "&orderId=" + payment_online.order_payment_id + "&partnerCode=" + MOMO_CONFIG.get(
                    "partnerCode") +
                                "&requestId=" + payment_online.request_payment_id)

                h = hmac.new(bytes(MOMO_CONFIG.get("secretKey"), 'ascii'), bytes(rawSignature, 'ascii'), hashlib.sha256)
                signature = h.hexdigest()

                data = {
                    'partnerCode': MOMO_CONFIG.get("partnerCode"),
                    'orderId': payment_online.order_payment_id,
                    'requestId': payment_online.request_payment_id,
                    'signature': signature,
                    'lang': MOMO_CONFIG.get("lang"),
                }
                response = requests.post(MOMO_CONFIG.get("momo_api_check_payment"), json=data,
                                         headers={'Content-Type': 'application/json'})
                data = response.json()

                if isinstance(data, dict):
                    if payment_online.result_payment is None:
                        payment_online.result_payment = data
                        if data.get('resultCode', None) == MOMO_CONFIG.get("status_success"):
                            payment_online.status_payment = True

                        db.session.flush()
                        db.session.commit()
                    else:
                        if isinstance(payment_online.result_payment, dict):
                            current_result_code = payment_online.result_payment.get('resultCode', None)
                            if current_result_code != MOMO_CONFIG.get("status_success") and data.get('resultCode',
                                                                                                     None) == MOMO_CONFIG.get(
                                    "status_success"):
                                payment_online.result_payment = data
                                payment_online.status_payment = True
                                db.session.flush()
                                db.session.commit()

            return send_result(data=PaymentOnlineSchema().dump(payment_online), message="Kết quả giao dịch")
        except Exception as ex:
            return send_result(data=PaymentOnlineSchema().dump(payment_online), message=str(ex))

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))


@api.route("/session/<session_id>", methods=['GET'])
@authorization_require()
def check_payment_session(session_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Người dùng không hợp lệ.')
        session_order = SessionOrder.query.filter(SessionOrder.id == session_id).first()
        if session_order is None:
            return send_error(message='Phiên thanh toán không tồn tại')

        payment_online = PaymentOnline.query.filter_by(session_order_id=session_id,status_payment=True).first()

        if payment_online:
            return send_result(data={'paid': True})
        return send_result(data={'paid': False})
    except Exception as ex:
        return send_error(message=str(ex))

#momo create payment
@api.route("/<session_id>", methods=['POST'])
@authorization_require()
def create_payment(session_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Người dùng không hợp lệ.')
        session_order = SessionOrder.query.filter( SessionOrder.id == session_id,
                                                        SessionOrder.duration > get_timestamp_now(),
                                                        SessionOrder.is_delete == False).first()
        if session_order is None:
            return send_error(message='Phiên thanh toán đã hết hạn')



        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = PaymentValidation()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')

        address_order_id = json_req.get('address_order_id')
        ship_id = json_req.get('ship_id', '')
        payment_type= json_req.get('payment_type')


        shipper = Shipper.query.filter(Shipper.id == ship_id).first()
        if shipper is None:
            return send_error(message='Shipper hiện giờ không làm việc.')

        address_order = AddressOrder.query.filter_by(user_id=user_id, id=address_order_id).first()
        if address_order is None:
            return send_error(message='Vui lòng thêm địa chỉ địa chỉ.')

        province = address_order.address.get('province')
        region_id = ''
        for key, value in regions.items():
            if province in value:
                region_id = key
                break

        find_price = PriceShip.query.filter_by(region_id=region_id, shipper_id=shipper.id).first()
        amount =  find_price.price + sum(
            item.cart_detail.quantity * item.cart_detail.product.detail.get('price', 0)
            for item in session_order.items
        )

        ### phần payment
        payment_online_id = str(uuid())
        order_payment_id = str(uuid())
        if payment_type == TYPE_PAYMENT_ONLINE.get('MOMO', 'momo'):
            request_id = str(uuid())
            ipnUrl = f"{CONFIG.BASE_URL_WEBSITE}/api/v1/payment_online/{TYPE_PAYMENT_ONLINE.get('MOMO', 'momo')}/{payment_online_id}/payment_notify"
            orderInfo = f"Pay with MoMo #{request_id}"
            # Trang momo đt chuyển đến link web mình muốn
            # redirectUrl = f"https://www.facebook.com/"
            # Trang momo đt không làm gì sau khi thanh toán

            rawSignature = "accessKey=" + MOMO_CONFIG.get("accessKey") + "&amount=" + str(
                amount) + "&extraData=" + MOMO_CONFIG.get("extraData") + "&ipnUrl=" + ipnUrl + "&orderId=" + order_payment_id \
                           + "&orderInfo=" + orderInfo + "&partnerCode=" + MOMO_CONFIG.get(
                "partnerCode") + "&redirectUrl=" + MOMO_CONFIG.get("redirectUrl") \
                           + "&requestId=" + request_id + "&requestType=" + MOMO_CONFIG.get("requestType")

            signature = hmac.new(bytes(MOMO_CONFIG.get("secretKey"), 'ascii'), bytes(rawSignature, 'ascii'), hashlib.sha256).hexdigest()
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
                'orderId': order_payment_id,
                'orderInfo': orderInfo,
                'requestId': request_id,
                'ipnUrl': ipnUrl,
                'amount': str(amount),
                'signature': signature
            }
            response = requests.post(MOMO_CONFIG.get("momo_api_create_payment"), data=json.dumps(data),
                                     headers={'Content-Type': 'application/json', 'Content-Length': str(len(data))})
            result = response.json()
            data_result = {
                'result': result,
                'payment_online_id': payment_online_id,
                'amount': amount,
                'description': orderInfo
            }
            if result.get("payUrl", None) and result.get("resultCode", None) == MOMO_CONFIG.get("status_success"):
                data_result['pay_url'] = result.get("payUrl")

        else:
            request_id = "{:%y%m%d}_{}".format(datetime.today(), get_timestamp_now())
            callback_url = f"{CONFIG.BASE_URL_WEBSITE}/api/v1/payment_online/{TYPE_PAYMENT_ONLINE.get('ZALO', 'zalo')}/{payment_online_id}/payment_notify"

            order = {
                "app_id": ZALO_CONFIG.get("app_id"),
                "app_trans_id": request_id,  # mã giao dich có định dạng yyMMdd_xxxx
                "app_user": ZALO_CONFIG.get("app_user"),
                "app_time": int(round(time() * 1000)),  # miliseconds
                "embed_data": json.dumps({}),
                "item": json.dumps([{}]),
                "amount": amount,
                "description": f"Pay with Zalo #{request_id}",
                "bank_code": ZALO_CONFIG.get("bank_code"),
                "callback_url": callback_url
            }

            # app_id|app_trans_id|app_user|amount|apptime|embed_data|item
            raw_signature = "{}|{}|{}|{}|{}|{}|{}".format(order["app_id"], order["app_trans_id"], order["app_user"],
                                                          order["amount"], order["app_time"], order["embed_data"],
                                                          order["item"])

            # signature
            mac_signature = hmac.new(ZALO_CONFIG['key1'].encode(), raw_signature.encode(), hashlib.sha256).hexdigest()
            order["mac"] = mac_signature
            # set link callback
            response = requests.post(ZALO_CONFIG.get("zalo_api_create_payment"), data=order)
            result = response.json()
            data_result = {
                'result': result,
                'payment_online_id': payment_online_id,
                'amount': amount,
                'description': order.get("description")
            }
            if result.get("order_url", None) and result.get("return_code", None) == ZALO_CONFIG.get("status_success"):
                data_result['pay_url'] = result.get("order_url")

        payment_online = PaymentOnline(id=payment_online_id, session_order_id=session_id,
                                       type=payment_type,
                                       order_payment_id=order_payment_id, request_payment_id=request_id)
        db.session.add(payment_online)
        db.session.flush()
        db.session.commit()
        return send_result(data=data_result)
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))


# #momo create payment
# @api.route("/momo", methods=['POST'])
# def momo_create_payment():
#     try:
#         orderId = str(uuid())
#         amount = 500
#         requestId = str(uuid())
#         payment_online_id = str(uuid())
#         ipnUrl = f"{CONFIG.BASE_URL_WEBSITE}/api/v1/payment_online/{TYPE_PAYMENT_ONLINE.get('MOMO', 'momo')}/{payment_online_id}/payment_notify"
#         orderInfo = f"Pay with MoMo #{requestId} ID-{payment_online_id}"
#         # Trang momo đt chuyển đến link web mình muốn
#         # redirectUrl = f"https://www.facebook.com/"
#         # Trang momo đt không làm gì sau khi thanh toán
#
#         rawSignature = "accessKey=" + MOMO_CONFIG.get("accessKey") + "&amount=" + str(
#             amount) + "&extraData=" + MOMO_CONFIG.get("extraData") + "&ipnUrl=" + ipnUrl + "&orderId=" + orderId \
#                        + "&orderInfo=" + orderInfo + "&partnerCode=" + MOMO_CONFIG.get(
#             "partnerCode") + "&redirectUrl=" + MOMO_CONFIG.get("redirectUrl") \
#                        + "&requestId=" + requestId + "&requestType=" + MOMO_CONFIG.get("requestType")
#
#         h = hmac.new(bytes(MOMO_CONFIG.get("secretKey"), 'ascii'), bytes(rawSignature, 'ascii'), hashlib.sha256)
#         signature = h.hexdigest()
#
#         payment_momo = PaymentOnline(id=payment_online_id,
#                                      type=TYPE_PAYMENT_ONLINE.get('MOMO', 'momo'),
#                                      order_payment_id=orderId, request_payment_id=requestId)
#         db.session.add(payment_momo)
#         db.session.flush()
#         db.session.commit()
#
#         data = {
#             'partnerCode': MOMO_CONFIG.get("partnerCode"),
#             'partnerName': MOMO_CONFIG.get("partnerName"),
#             'storeId': MOMO_CONFIG.get("storeId"),
#             'extraData': MOMO_CONFIG.get("extraData"),
#             'orderGroupId': MOMO_CONFIG.get("orderGroupId"),
#             'lang': MOMO_CONFIG.get("lang"),
#             'requestType': MOMO_CONFIG.get("requestType"),
#             'redirectUrl': MOMO_CONFIG.get("redirectUrl"),
#             'autoCapture': MOMO_CONFIG.get("autoCapture"),
#             'orderId': orderId,
#             'orderInfo': orderInfo,
#             'requestId': requestId,
#             'ipnUrl': ipnUrl,
#             'amount': str(amount),
#             'signature': signature
#         }
#
#         data = json.dumps(data)
#
#         clen = len(data)
#         response = requests.post(MOMO_CONFIG.get("momo_api_create_payment"), data=data,
#                                  headers={'Content-Type': 'application/json', 'Content-Length': str(clen)})
#         # Trả về phản hồi
#         data = response.json()
#
#         data_result = {
#             'result': data,
#             'payment_online_id': payment_online_id,
#
#         }
#         if data.get("payUrl", None) and data.get("resultCode", None) == 0:
#             data_result['pay_url'] = data.get("payUrl")
#
#         return send_result(data=data_result)
#     except Exception as ex:
#         db.session.rollback()
#         return send_error(message=str(ex))
#
# #zalo
# @api.route("/zalo", methods=['POST'])
# def zalo_create_payment():
#     try:
#
#         orderId = str(uuid())
#         amount = 500
#         request_id = "{:%y%m%d}_{}".format(datetime.today(), get_timestamp_now())
#         payment_online_id = str(uuid())
#
#         order = {
#             "app_id": ZALO_CONFIG.get("app_id"),
#             "app_trans_id": request_id ,  # mã giao dich có định dạng yyMMdd_xxxx
#             "app_user": ZALO_CONFIG.get("app_user"),
#             "app_time": int(round(time() * 1000)),  # miliseconds
#             "embed_data": json.dumps({}),
#             "item": json.dumps([{}]),
#             "amount": amount,
#             "description": f"Pay with Zalo #{request_id} ID-{payment_online_id}",
#             "bank_code": ZALO_CONFIG.get("bank_code"),
#         }
#
#         # app_id|app_trans_id|app_user|amount|apptime|embed_data|item
#         raw_signature = "{}|{}|{}|{}|{}|{}|{}".format(order["app_id"], order["app_trans_id"], order["app_user"],
#                                              order["amount"], order["app_time"], order["embed_data"], order["item"])
#
#         # signature
#         mac_signature = hmac.new(ZALO_CONFIG['key1'].encode(), raw_signature.encode(), hashlib.sha256).hexdigest()
#         order["mac"] = mac_signature
#
#         payment_zalo = PaymentOnline(id=payment_online_id, order_payment_id=orderId, request_payment_id=request_id,
#                                      type=TYPE_PAYMENT_ONLINE.get('ZALO', 'zalo'),)
#
#         # set link callback
#         callback_url = f"{CONFIG.BASE_URL_WEBSITE}/api/v1/payment_online/{TYPE_PAYMENT_ONLINE.get('ZALO', 'zalo')}/{payment_zalo.id}/payment_notify"
#         order["callback_url"] = callback_url
#
#
#         db.session.add(payment_zalo)
#         db.session.flush()
#         db.session.commit()
#
#         response = requests.post(ZALO_CONFIG.get("zalo_api_create_payment"), data=order)
#
#         # Đọc kết quả JSON
#         result = response.json()
#
#         data_result = {
#             'result': result,
#             'payment_online_id': payment_online_id,
#         }
#
#         if result.get("order_url", None) and result.get("return_code", None) == 1:
#             data_result['pay_url'] = result.get("order_url")
#
#         return send_result(data=data_result)
#     except Exception as ex:
#         db.session.rollback()
#         return send_error(message=str(ex))