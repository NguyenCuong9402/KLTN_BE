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
from app.enums import PROMPT_AI
from app.generativeai import search_ai
from app.message_broker import RabbitMQProducerGenerateSearchProduct
from app.models import db, Product, TypeProduct
from app.settings import DevConfig
from app.utils import trim_dict, escape_wildcard
from app.validator import ProductSchema, QueryParamsSchema, QueryParamsProductAiSchema

api = Blueprint('product', __name__)

@api.route("/<product_id>", methods=["GET"])
def get_item(product_id):
    try:
        item = Product.query.filter(Product.id == product_id, Product.is_delete.is_(False)).first()
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
        select_type = params.get('select_type', [])

        query = Product.query.filter(Product.is_delete.is_(False))

        if select_type:
            query = query.filter(Product.type_product_id.in_(select_type))

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


@api.route("/search_by_ai", methods=["GET"])
@jwt_required
def get_items_ai():
    try:

        text_search = request.args.get('text_search', '')

        query = Product.query.filter(Product.is_delete.is_(False))

        if not text_search:
            return send_error(message='Không được để trống')

        names = (db.session.query(TypeProduct.name).filter(TypeProduct.type_id.isnot(None))
                 .order_by(asc(TypeProduct.key)).all())
        name_type_list = [name for (name,) in names]

        result = search_ai(PROMPT_AI, text_search, name_type_list)

        max_price = result.get('max_price', None)
        min_price = result.get('min_price', None)
        list_type =  result.get('type', [])

        type_finds = TypeProduct.query.filter(TypeProduct.name.in_(list_type)).all()

        type_list = [type_find.id for type_find in type_finds]

        if type_list:
            query = query.filter(Product.type_product_id.in_(type_list))

        if isinstance(min_price, (int, float)):
            query = query.filter(Product.original_price >= min_price)

        if isinstance(max_price, (int, float)):
            query = query.filter(Product.original_price <= max_price)

        query = query.order_by(desc(Product.original_price))


        products = ProductSchema(many=True).dump(query.all())


        return send_result(data=products)
    except Exception as ex:
        return send_error(message=str(ex))
