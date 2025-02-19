import json
from shortuuid import uuid
from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy import desc, asc
from sqlalchemy_pagination import paginate

from app.enums import TYPE_FILE_LINK
from app.extensions import logger, db
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.api.helper import send_result, send_error
from app.models import Product, Size, Color, \
    FileLink
from app.utils import trim_dict, escape_wildcard, get_timestamp_now
from app.validator import ProductValidation, ProductSchema, QueryParamsSchema

api = Blueprint('manage/product', __name__)


@api.route('', methods=['POST'])
@jwt_required
def new():
    try:

        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = ProductValidation()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')

        files = json_body.pop('files')
        sizes = json_body.pop('sizes')
        colors = json_body.pop('colors')

        product = Product(**json_body, id=str(uuid()))
        db.session.add(product)
        db.session.flush()

        size_objects = [Size(id=str(uuid()), name=size, product_id=product.id, index=index,
                             created_date=get_timestamp_now()+index) for index, size in enumerate(sizes)]
        color_objects = [Color(id=str(uuid()), name=color, product_id=product.id, index=index,
                               created_date=get_timestamp_now()+index) for index, color in enumerate(colors)]
        db.session.bulk_save_objects(size_objects)
        db.session.bulk_save_objects(color_objects)
        db.session.flush()

        file_objects = [FileLink(id=str(uuid()), table_id=product.id, file_id=file["id"],
                                 table_type=TYPE_FILE_LINK.get('PRODUCT', 'product'),
                                 index=index, created_date=get_timestamp_now()+index)
                        for index, file in enumerate(files)]
        db.session.bulk_save_objects(file_objects)
        db.session.flush()

        db.session.commit()
        return send_result(message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


def check_coincided_name_product(name='', product_id=''):
    existed_name = Product.query.filter(Product.name == name)
    if product_id:
        existed_name = existed_name.filter(Product.id != product_id)
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
