from shortuuid import uuid
from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy import desc, asc, or_
from sqlalchemy_pagination import paginate

from app.extensions import db
from app.api.helper import send_result, send_error
from app.gateway import authorization_require
from app.models import TypeProduct, Product
from app.utils import trim_dict, escape_wildcard
from app.validator import TypeProductValidation, QueryParamsAllSchema, TypeProductSchema

api = Blueprint('manage/type_product', __name__)


@api.route('', methods=['POST'])
@authorization_require()
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

        if check_coincided_key(json_req['key']):
            return send_error(message='Key đã tồn tại')

        type_product = TypeProduct(**json_body, id=str(uuid()))
        db.session.add(type_product)
        db.session.flush()


        db.session.commit()
        return send_result(message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


@api.route('/<id_type>', methods=['PUT'])
@authorization_require()
def put(id_type):
    try:

        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = TypeProductValidation()
        is_not_validate = validator_input.validate(json_body)

        type_product = TypeProduct.query.filter_by(id=id_type).first()

        if type_product is None:
            return send_error(message='Loại sản phẩm không tồn tại')

        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')

        if check_coincided_name(json_req['name'], id_type):
            return send_error(message='Tên đã tồn tại')

        if check_coincided_key(json_req['key'], id_type):
            return send_error(message='Key đã tồn tại')

        type_product.key = json_req['key']
        type_product.name = json_req['name']
        type_product.type_id = json_req['type_id']

        db.session.flush()
        db.session.commit()

        data = TypeProductSchema().dump(type_product)


        return send_result(data=data, message='Thành công')

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


def check_coincided_key(key='', type_id=''):
    existed_key = TypeProduct.query.filter(TypeProduct.key == key)
    if type_id:
        existed_key = existed_key.filter(TypeProduct.id != type_id)
    if existed_key.first() is None:
        return False
    return True



@api.route("", methods=["DELETE"])
@authorization_require()
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

@api.route("/<type_id>", methods=["DELETE"])
@authorization_require()
def remove_item_id(type_id):
    try:
        Product.query.filter(Product.id == type_id).delete()
        db.session.flush()
        db.session.commit()
        return send_result(message="Xóa sản phẩm thành công")
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))


@api.route("/get_parent", methods=["GET"])
def get_parent_type():
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = QueryParamsAllSchema().load(params) if params else dict()
        except ValidationError as err:
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)


        page = params.get('page', 1)
        page_size = params.get('page_size', 10)
        order_by = params.get('order_by', 'created_date')
        sort = params.get('sort', 'desc')
        text_search = params.get('text_search', None)

        query = TypeProduct.query.filter(TypeProduct.type_id.is_(None))
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



@api.route("/get_all", methods=["GET"])
def get_all():
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = QueryParamsAllSchema().load(params) if params else dict()
        except ValidationError as err:
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)


        page = params.get('page', 1)
        page_size = params.get('page_size', 20)
        sort = params.get('sort', 'desc')
        text_search = params.get('text_search', None)

        query = TypeProduct.query.filter()
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


        query = query.order_by(desc(TypeProduct.name)) if sort == "desc" else query.order_by(asc(TypeProduct.name))

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

