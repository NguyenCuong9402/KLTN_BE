import json
from shortuuid import uuid
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import asc, desc

from app.api.helper import send_result, send_error
from app.enums import regions, TYPE_PAYMENT_ONLINE
from app.models import db, User, SessionOrder, SessionOrderCartItems, Orders, OrderItems, CartItems, AddressOrder, \
    PriceShip, Shipper, PaymentOnline
from app.utils import get_timestamp_now, trim_dict
from app.validator import CartSchema, SessionSchema, ShipperSchema, AddressOrderSchema, PaymentValidation, \
    SessionOrderValidate

api = Blueprint('session_order', __name__)


@api.route('', methods=['POST'])
@jwt_required
def add_item_to_session():
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Người dùng không hợp lệ.')
        json_body = request.get_json()

        list_cart_id = json_body.get('list_cart_id', [])

        if len(list_cart_id) == 0:
            return send_error(message='Chưa chọn sản phẩm thanh toán.')

        session = SessionOrder(id=str(uuid()), user_id=user_id)
        db.session.add(session)
        db.session.flush()


        list_session_order_cart = [SessionOrderCartItems(id=str(uuid()),index=index,cart_id=cart_id,
                                                         session_order_id=session.id)
                                   for index, cart_id in enumerate(list_cart_id)]

        db.session.bulk_save_objects(list_session_order_cart)
        db.session.flush()
        db.session.commit()
        return send_result(data= {"id": session.id} ,message='Thành công.')
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


@api.route("/<session_id>", methods=["GET"])
@jwt_required
def get_items_in_session(session_id):
    try:
        address_order_id = request.args.get('address_order_id', None)
        user_id=get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Người dùng không hợp lệ.')
        session = SessionOrder.query.filter(SessionOrder.user_id==user_id, SessionOrder.id == session_id,
                                          SessionOrder.duration > get_timestamp_now(), SessionOrder.is_delete == False
                                            ).first()
        if session is None:
            return send_error(message='Phiên thanh toán đã hết hạn')
        items = session.items


        shipper = Shipper.query.filter().order_by(asc(Shipper.index)).first()
        if shipper is None:
            return send_error(message='Shipper hiện giờ không làm việc.')

        # Tìm địa chỉ ship
        price_ship = 0
        data_address_order = None

        if address_order_id:
            address_order = AddressOrder.query.filter_by(user_id=user_id, id=address_order_id).first()
            if address_order :
                province = address_order.address.get('province')
                region_id = ''
                for key, value in regions.items():
                    if province in value:
                        region_id = key
                        break

                find_price = PriceShip.query.filter_by(region_id=region_id, shipper_id=shipper.id).first()
                data_address_order = AddressOrderSchema().dump(address_order)
                price_ship = find_price.price

        price_product = sum(item.cart_detail.quantity * item.cart_detail.product.detail.get('price', 0)
                            for item in items)

        total = price_product + price_ship


        session_data = SessionSchema().dump(session)
        session_data.update({
            'price_product': price_product,
            'total': total,
            'price_ship': price_ship,
            'shipper': ShipperSchema().dump(shipper),
            'address_order': data_address_order
        })
        return send_result(data=session_data)
    except Exception as ex:
        return send_error(message=str(ex))

@api.route("/update_ship/<session_id>", methods=["PUT"])
@jwt_required
def update_ship_in_session(session_id):
    try:
        user_id=get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Người dùng không hợp lệ.')
        session = SessionOrder.query.filter(SessionOrder.user_id==user_id, SessionOrder.id == session_id,
                                          SessionOrder.duration > get_timestamp_now(), SessionOrder.is_delete == False
                                            ).first()
        if session is None:
            return send_error(message='Phiên thanh toán đã hết hạn')

        body_request = request.get_json()

        shipper_id = body_request.get('shipper_id')
        address_order_id = body_request.get('address_order_id')


        shipper = Shipper.query.filter_by(id=shipper_id).first()

        if shipper is None:
            return send_error(message='Shipper hiện giờ không làm việc.')

        # Tìm địa chỉ mặc định và gán.
        address_order = AddressOrder.query.filter_by(user_id=user_id, id=address_order_id).first()
        if address_order is None:
            price_ship = 0
        else:
            province = address_order.address.get('province')
            region_id = ''
            for key, value in regions.items():
                if province in value:
                    region_id = key
                    break

            find_price = PriceShip.query.filter_by(region_id=region_id, shipper_id=shipper.id).first()
            price_ship = find_price.price

        price_product = 0
        for index, item in enumerate(session.items):
            count_item = item.cart_detail.quantity * item.cart_detail.product.detail.get('price', 0)
            price_product += count_item

        total = price_product + price_ship

        session_data = SessionSchema().dump(session)
        session_data.update({
            'price_product': price_product,
            'total': total,
            'price_ship': price_ship,
            'shipper': ShipperSchema().dump(shipper),
        })
        return send_result(data=session_data)
    except Exception as ex:
        return send_error(message=str(ex))

@api.route("/<session_id>", methods=["POST"])
@jwt_required
def order_session(session_id):
    try:
        user_id=get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Người dùng không hợp lệ.')
        session_order = SessionOrder.query.filter(SessionOrder.user_id == user_id, SessionOrder.id == session_id,
                                                        SessionOrder.duration > get_timestamp_now(),
                                                        SessionOrder.is_delete == False).first()

        if session_order is None:
            return send_error(message='Phiên thanh toán đã hết hạn')

        json_request = request.get_json()

        json_body = trim_dict(json_request)
        validator_input = SessionOrderValidate()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')

        message = json_body.get('message')
        address_order_id = json_body.get('address_order_id')
        ship_id = json_body.get('ship_id')
        payment_type = json_body.get('payment_type')
        payment_online_id = json_body.get('payment_online_id', None)
        if payment_type in  TYPE_PAYMENT_ONLINE.values():
            payment_online = PaymentOnline.query.filter_by(id=payment_online_id).first()
            if payment_online is None:
                return send_error(message='Không tìm thấy thanh toán trước đó.')

        shipper = Shipper.query.filter(Shipper.id==ship_id).first()
        if shipper is None:
            return send_error(message='Shipper hiện giờ không làm việc.')


        address_order = AddressOrder.query.filter_by(user_id=user_id, id=address_order_id).first()
        if address_order is None:
            return send_error(message='Vui lòng thêm địa chỉ địa chỉ. ')

        province = address_order.address.get('province')
        region_id = ''
        for key, value in regions.items():
            if province in value:
                region_id = key
                break

        find_price = PriceShip.query.filter_by(region_id=region_id, shipper_id=shipper.id).first()
        price_ship = find_price.price

        order = Orders(id=str(uuid()), user_id=user_id, phone_number=address_order.phone,
                       message=message, ship_id=ship_id, price_ship=price_ship,
                       full_name=address_order.full_name, detail_address=address_order.detail_address,
                       address_id=address_order.address_id)

        db.session.add(order)
        db.session.flush()

        items = session_order.items
        count = price_ship

        for index, item in enumerate(items):
            count_item = item.cart_detail.quantity * item.cart_detail.product.detail.get('price', 0)
            order_item = OrderItems(id=str(uuid()), created_date=get_timestamp_now()+index, order_id=order.id,
                                    quantity=item.cart_detail.quantity, color_id=item.cart_detail.color_id,
                                    size_id=item.cart_detail.size_id, product_id=item.cart_detail.product_id,
                                    count=count_item)
            count += count_item
            db.session.add(order_item)
            CartItems.query.filter(CartItems.id==item.cart_id).delete()
            db.session.flush()

        session_order.is_delete = True
        order.count = count
        if payment_type in  TYPE_PAYMENT_ONLINE.values():
            order.payment_status = True
            order.payment_online_id = payment_online_id

        db.session.flush()
        db.session.commit()

        return send_result(message='Đặt hàng thành công.', data={'count': count, 'price_ship': price_ship})
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))




