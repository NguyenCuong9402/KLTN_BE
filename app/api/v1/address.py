from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import asc

from app.api.helper import send_error, send_result, Token
from app.models import Address, User, AddressOrder
from shortuuid import uuid
from app.extensions import jwt, db
from app.validator import AddressOrderSchema

api = Blueprint('address', __name__)

@api.route("", methods=["GET"])
def get_address():
    try:
        province = request.args.get('province', "")
        district = request.args.get('district', "")

        data = {}
        address_provinces = Address.query.with_entities(Address.province).distinct().order_by(Address.province).all()
        data['province'] = [address_province.province for address_province in address_provinces]

        address_districts = Address.query.filter(Address.province == province) \
            .with_entities(Address.district) \
            .distinct().order_by(Address.district).all()

        data['district'] = [address_district.district for address_district in address_districts]

        address_wards = Address.query.filter(Address.province == province, Address.district == district) \
            .with_entities(Address.ward).distinct().order_by(Address.ward).all()
        data['ward'] = [address_ward.ward for address_ward in address_wards]

        return send_result(message='Done', data=data)
    except Exception as ex:
        return send_error(message=str(ex))


@api.route("/add_address", methods=["POST"])
@jwt_required
def post_address_order():
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Tài khoản không hợp lệ.')
        body_request = request.get_json()
        province = body_request.get('province', "")
        district = body_request.get('district', "")
        ward = body_request.get('ward', "")
        detail_address = body_request.get('detail_address', "")

        full_name = body_request.get('full_name', "")
        phone = body_request.get('phone', "")

        if "" in [full_name, phone, province, district, ward, detail_address]:
            return send_error(message='Bạn chưa nhập đầy đủ thông tin')


        address_check = Address.query.filter_by(province=province, district=district,
                                          ward=ward).first()


        user_address = AddressOrder.query.filter_by(user_id=user_id)

        check_user_address = user_address.filter_by(address_id=address_check.id).first()

        if check_user_address:
            return send_error(message='Bạn đã có địa chỉ này, vui lòng chọn địa chỉ khác.')

        if user_address.count() == 0:
            index_address = 0
            default = True
        else:
            if user_address.count() >= 10:
                return send_error(message='Danh sách không lưu quá 10 địa chỉ.')
            else:
                index_address = user_address.count()
                default = False

        address_order = AddressOrder(id=str(uuid()), address_id=address_check.id,full_name=full_name,
                                     detail_address=detail_address, phone=phone,
                                     user_id=user_id, index=index_address, default=default)
        db.session.add(address_order)
        db.session.flush()
        db.session.commit()
        data = AddressOrderSchema().dump(address_order)
        return send_result(message='Done', data=data)
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))


@api.route("/address_order", methods=["GET"])
@jwt_required
def get_address_order():
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Tài khoản không hợp lệ.')
        user_address = AddressOrder.query.filter_by(user_id=user_id).order_by(asc(AddressOrder.index))
        data = AddressOrderSchema(many=True).dump(user_address)

        return send_result(message='Done', data=data)
    except Exception as ex:
        return send_error(message=str(ex))

@api.route("/address_order_main", methods=["GET"])
@jwt_required
def address_order_main():
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Tài khoản không hợp lệ.')
        user_address = AddressOrder.query.filter_by(user_id=user_id, default=True).first()

        if user_address:
            data = AddressOrderSchema().dump(user_address)
            return send_result(message='Thành công', data=data)

        return send_result(message='Chưa có địa chỉ mặc định')

    except Exception as ex:
        return send_error(message=str(ex))


@api.route("/remove_address", methods=["DELETE"])
@jwt_required
def remove_item():
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Tài khoản không hợp lệ.')
        body_request = request.get_json()
        list_id = body_request.get('list_id', [])
        if len(list_id) == 0:
            return send_error(message='Chưa chọn item nào.')
        AddressOrder.query.filter(AddressOrder.id.in_(list_id),AddressOrder.user_id==user_id).delete()
        db.session.flush()

        address_orders = AddressOrder.query.filter(AddressOrder.user_id==user_id).order_by(asc(AddressOrder.index)).all()

        for index, address_order in enumerate(address_orders):
            address_order.index = index
            db.session.flush()
        db.session.commit()
        data = AddressOrderSchema(many=True).dump(address_orders)

        return send_result(message="Xóa sản phẩm thành công", data=data)
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))


@api.route("/choose_default/<address_order_id>", methods=["PUT"])
@jwt_required
def choose_default(address_order_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Tài khoản không hợp lệ.')
        user_address = AddressOrder.query.filter(user_id==user_id, AddressOrder.id==address_order_id).first()

        if user_address is None:
            return send_error(message='Chọn mặc định không thành công, vui lòng tải lại trang')

        user_address.default = True
        db.session.flush()
        AddressOrder.query.filter(
            AddressOrder.user_id == user_id,
            AddressOrder.id != address_order_id
        ).update({"default": False})
        db.session.flush()

        db.session.commit()
        data = AddressOrderSchema().dump(user_address)

        return send_result(message='Done', data=data)
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))





