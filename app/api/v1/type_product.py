from operator import or_

from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy import asc, desc
from sqlalchemy.orm import joinedload
from sqlalchemy_pagination import paginate

from app.api.helper import send_result, send_error
from app.models import TypeProduct
from app.utils import escape_wildcard
from app.validator import TypeProductWithChildrenSchema, TypeProductSchema, ParamTypeProduct

api = Blueprint('type_product', __name__)


@api.route("/get_filter", methods=["GET"])
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


@api.route("", methods=["GET"])
def get_all_type():
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = ParamTypeProduct().load(params) if params else dict()
        except ValidationError as err:
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)

        page = params.get('page', 1)
        page_size = params.get('page_size', 50)
        order_by = params.get('order_by', 'name')
        sort = params.get('sort', 'asc')
        text_search = params.get('text_search', None)
        type_id = params.get('type_id', None)

        query = TypeProduct.query.filter(TypeProduct.type_id.isnot(None))

        if type_id:
            check = TypeProduct.query.filter_by(id=type_id).first()

            if check is None:
                return send_error(message='Loại sản phẩm không tồn tại')

            query = query.filter(TypeProduct.type_id == type_id)

        if text_search:
            text_search = text_search.strip()
            text_search = text_search.lower()
            text_search = escape_wildcard(text_search)
            text_search = "%{}%".format(text_search)

            query = query.filter(
                or_(
                    TypeProduct.name.ilike(f"%{text_search}%"),
                    TypeProduct.key.ilike(f"%{text_search}%")
                )
            )

        column_sorted = getattr(TypeProduct, order_by)

        query = query.order_by(desc(column_sorted)) if sort == "desc" else query.order_by(asc(column_sorted))

        paginator = paginate(query, page, page_size)

        type_products = TypeProductSchema(many=True).dump(paginator.items)

        response_data = dict(
            items=type_products,
            total_pages=paginator.pages if paginator.pages > 0 else 1,
            total=paginator.total,
            has_previous=paginator.has_previous,
            has_next=paginator.has_next
        )
        return send_result(data=response_data)
    except Exception as ex:
        return send_error(message=str(ex))