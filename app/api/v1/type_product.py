from flask import Blueprint
from sqlalchemy import asc
from sqlalchemy.orm import joinedload
from app.api.helper import send_result, send_error
from app.models import TypeProduct, Product
from app.validator import TypeProductWithChildrenSchema, TypeProductSchema

api = Blueprint('type_product', __name__)


@api.route("", methods=["GET"])
def get_parent_type():
    try:
        query = (TypeProduct.query.filter(TypeProduct.type_id.is_(None))
                 .options(joinedload(TypeProduct.type_child)).order_by(asc(TypeProduct.key)).all())

        type_products = TypeProductWithChildrenSchema(many=True).dump(query)

        return send_result(data=type_products)
    except Exception as ex:
        return send_error(message=str(ex))

@api.route("/<type_id>", methods=["GET"])
def get_detail_type(type_id):
    try:
        check = TypeProduct.query.filter_by(id=type_id).first()
        if check is None:
            return send_error(message='Loại sản phẩm không tồn tại')
        type_product = TypeProductSchema().dump(check)
        return send_result(data=type_product)
    except Exception as ex:
        return send_error(message=str(ex))
