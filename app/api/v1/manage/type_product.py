import json
from shortuuid import uuid
from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy import desc, asc
from sqlalchemy_pagination import paginate

from app.extensions import logger, db
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.api.helper import send_result, send_error
from app.models import TypeProduct, Product
from app.utils import trim_dict, escape_wildcard, get_timestamp_now
from app.validator import ProductValidation, ProductSchema, QueryParamsSchema, TypeProductValidation

api = Blueprint('manage/type_product', __name__)


@api.route('', methods=['POST'])
@jwt_required
def new():
    try:

        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = TypeProductValidation()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')

        if check_coincided_name(json_req['name']):
            return send_error(message='Tên đã tồn tại')
        type_product = TypeProduct(**json_body, id=str(uuid()))
        db.session.add(type_product)
        db.session.flush()


        db.session.commit()
        return send_result(message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)

def check_coincided_name(name='', type_id=''):
    existed_name = TypeProduct.query.filter(TypeProduct.name == name)
    if type_id:
        existed_name = existed_name.filter(TypeProduct.id != type_id)
    if existed_name.first() is None:
        return False
    return True



@api.route("", methods=["DELETE"])
@jwt_required
def remove_item():
    try:
        body_request = request.get_json()
        list_id = body_request.get('list_id', [])
        if len(list_id) == 0:
            return send_error(message='Chưa chọn item nào.')
        Product.query.filter(Product.id.in_(list_id)).delete()
        db.session.flush()
        db.session.commit()
        return send_result(message="Xóa sản phẩm thành công")
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))
