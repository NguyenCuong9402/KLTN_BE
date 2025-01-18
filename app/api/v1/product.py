import json
import os
import uuid
from uuid import uuid4

from flask import Blueprint, request, make_response, send_file, Response
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError
from sqlalchemy import asc, desc
from io import BytesIO
import datetime
import io

from sqlalchemy_pagination import paginate
from werkzeug.utils import secure_filename

from app.api.helper import send_result, send_error
from app.extensions import logger
from app.models import db, Product, User, Orders, OrderItems, CartItems, Files, TypeProduct
from app.utils import trim_dict, escape_wildcard
from app.validator import ProductValidation, TypeProductSchema, ProductSchema, QueryParamsSchema

api = Blueprint('product', __name__)


@api.route('/get_type', methods=['GET'])
def get_type():
    try:
        query=TypeProduct.query.filter().order_by(desc(TypeProduct.name)).all()
        data = TypeProductSchema(many=True).dump(query)
        return send_result(data=data, message='Thành công')
    except Exception as ex:
        return send_error(message=str(ex), code=442)

@api.route("/<product_id>", methods=["GET"])
def get_item(product_id):
    try:
        item = Product.query.filter(Product.id == product_id).first()
        if item is None:
            return send_error(message="Sản phẩm không tồn tại, F5 lại web")
        data = ProductSchema(many=False).dump(item)
        return send_result(data=data)
    except Exception as ex:
        return send_error(message=str(ex))

@api.route("", methods=["GET"])
def get_items():
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = QueryParamsSchema().load(params) if params else dict()
        except ValidationError as err:
            logger.error(json.dumps({
                "message": err.messages,
                "data": err.valid_data
            }))
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)
        from_money = params.get('from_money', None)
        to_money = params.get('to_money', None)
        from_date = params.get('from_date', None)
        to_date = params.get('to_date', None)
        page = params.get('page', 1)
        page_size = params.get('page_size', 10)
        order_by = params.get('order_by', 'created_date')
        sort = params.get('sort', 'desc')
        text_search = params.get('text_search', None)
        type_id = params.get('type_id', None)

        query = Product.query.filter()

        if type_id:
            check = TypeProduct.query.filter(TypeProduct.id == type_id).first()
            if check is None:
                return send_error(message='Loại không tồn tại')
            get_child_type = TypeProduct.query.filter(TypeProduct.type_id == type_id).all()
            list_id = [item.id for item in get_child_type]
            list_id.append(type_id)
            query = query.filter(Product.type_product_id.in_(list_id))

        if text_search:
            text_search = text_search.strip()
            text_search = text_search.lower()
            text_search = escape_wildcard(text_search)
            text_search = "%{}%".format(text_search)
            query = query.filter(Product.name.ilike(text_search))
        if from_money:
            query = query.filter(Product.original_price >= from_money)

        if to_money:
            query = query.filter(Product.original_price <= to_money)

        if from_date:
            query = query.filter(Product.created_date >= from_date)
        if to_date:
            query = query.filter(Product.created_date <= to_date)

        column_sorted = getattr(Product, order_by)

        query = query.order_by(desc(column_sorted)) if sort == "desc" else query.order_by(asc(column_sorted))

        paginator = paginate(query, page, page_size)

        products = ProductSchema(many=True).dump(paginator.items)

        response_data = dict(
            items=products,
            total_pages=paginator.pages if paginator.pages > 0 else 1,
            total=paginator.total,
            # current_page=paginator.page,  # Số trang hiện tại
            has_previous=paginator.has_previous,  # Có trang trước không
            has_next=paginator.has_next  # Có trang sau không
        )
        return send_result(data=response_data)
    except Exception as ex:
        return send_error(message=str(ex))
