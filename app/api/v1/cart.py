import json
from shortuuid import uuid
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError
from sqlalchemy import asc, desc
from datetime import datetime
from sqlalchemy_pagination import paginate

from app.api.helper import send_result, send_error
from app.extensions import logger
from app.models import CartItems, db, User
from app.utils import trim_dict, get_timestamp_now
from app.validator import QueryParamsAllSchema, CartSchema, CartValidation, CartUpdateValidation

api = Blueprint('cart', __name__)


@api.route('/add_item', methods=['POST'])
@jwt_required
def add_item_to_cart():
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Người dùng không hợp lệ.')
        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = CartValidation()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')
        check_item = CartItems.query.filter_by(product_id=json_body.get('product_id'), user_id=user_id,
                                               color_id=json_body.get('color_id'),
                                               size_id=json_body.get('size_id')).first()
        if check_item:
            check_item.quantity += json_body.get('quantity', 1)
            check_item.update_date = get_timestamp_now()
        else:
            item = CartItems(id=str(uuid()), **json_body, user_id=user_id)
            db.session.add(item)
        db.session.flush()
        db.session.commit()
        return send_result(message='Thêm giỏ hàng thành công.')
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


@api.route("", methods=["GET"])
@jwt_required
def get_items_in_cart():
    try:
        user_id=get_jwt_identity()
        try:
            params = request.args.to_dict(flat=True)
            params = QueryParamsAllSchema().load(params) if params else dict()
        except ValidationError as err:
            logger.error(json.dumps({
                "message": err.messages,
                "data": err.valid_data
            }))
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)
        page = params.get('page', 1)
        page_size = params.get('page_size', 10)
        order_by = 'modified_date'
        sort = 'desc'

        query = CartItems.query.filter(CartItems.user_id==user_id)
        column_sorted = getattr(CartItems, order_by)

        query = query.order_by(desc(column_sorted)) if sort == "desc" else query.order_by(asc(column_sorted))

        paginator = paginate(query, page, page_size)

        products = CartSchema(many=True).dump(paginator.items)

        response_data = dict(
            items=products,
            total_pages=paginator.pages if paginator.pages > 0 else 1,
            total=paginator.total,
            has_previous=paginator.has_previous,  # Có trang trước không
            has_next=paginator.has_next  # Có trang sau không
        )
        return send_result(data=response_data)
    except Exception as ex:
        return send_error(message=str(ex))

@api.route('/<cart_id>', methods=['PUT'])
@jwt_required
def put_item_to_cart(cart_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Người dùng không hợp lệ.')
        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = CartUpdateValidation()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')
        cart_item = CartItems.query.filter_by(id=cart_id).first()
        if cart_item is None:
            return send_error(message='Sản phẩm đã bị xóa, vui lòng F5.')

        quantity = json_body.get('quantity')
        color_id = json_body.get('color_id')
        size_id = json_body.get('size_id')
        product_id = json_body.get('product_id')
        check_cart_items = CartItems.query.filter(CartItems.id!=cart_id, CartItems.user_id==user_id,
                                                  CartItems.color_id == color_id, CartItems.product_id==product_id,
                                                  CartItems.size_id == size_id).all()
        cart_ids_remove = []
        for key, value in json_body.items():
            setattr(cart_item, key, value)
        if len(check_cart_items) > 0:
            for check_cart_item in check_cart_items:
                cart_item.quantity += check_cart_item.quantity
                cart_ids_remove.append(check_cart_item.id)
            CartItems.query.filter(CartItems.id.in_(cart_ids_remove)).delete()
            db.session.flush()

        db.session.flush()
        db.session.commit()

        cart_item = CartSchema().dump(cart_item)

        return send_result(message='Thêm giỏ hàng thành công.', data={'cart_ids_remove': cart_ids_remove,
                                                                      'cart_item': cart_item})
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


@api.route("/delete", methods=["DELETE"])
@jwt_required
def remove_item():
    try:
        user_id = get_jwt_identity()
        body_request = request.get_json()
        list_id = body_request.get('list_id', [])
        if len(list_id) == 0:
            return send_error(message='Chưa chọn item nào.')
        CartItems.query.filter(CartItems.user_id==user_id, CartItems.id.in_(list_id)).delete()
        db.session.flush()
        db.session.commit()
        return send_result(message="Bỏ thành công")
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))



