import json

from flask import Blueprint, request, make_response, send_file, Response
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError
from sqlalchemy import asc, desc

from sqlalchemy_pagination import paginate

from app.api.helper import send_result, send_error
from app.enums import KEY_GROUP_NOT_STAFF
from app.extensions import logger
from app.models import Group, TypeProduct, Product, Shipper, Orders, User
from app.utils import trim_dict, escape_wildcard
from app.validator import GroupSchema, QueryParamsAllSchema

api = Blueprint('statistic', __name__)


@api.route('/statistic_product_by_type', methods=['GET'])
@jwt_required
def get_number_product_by_type():
    try:

        data = [
            {
                "name": p.name,
                # "list_id": [p.id] + [child.id for child in p.type_child],
                "total": Product.query.filter(
                    Product.type_product_id.in_([p.id] + [child.id for child in p.type_child])).count()
            }
            for p in TypeProduct.query.filter(TypeProduct.type_id.is_(None)).all()
        ]

        return send_result(data=data, message="Thành công")
    except Exception as ex:
        return send_error(message=str(ex), code=442)


@api.route('/statistic_ship', methods=['GET'])
@jwt_required
def statistic_ship():
    try:

        data = [
            {
                "name": shipper.name,
                "total": Orders.query.filter(Orders.ship_id == shipper.id).count()
            }
            for shipper in Shipper.query.all()
        ]

        return send_result(data=data, message="Thành công")
    except Exception as ex:
        return send_error(message=str(ex), code=442)


@api.route('/statistic_user', methods=['GET'])
@jwt_required
def statistic_user():
    try:

        users = User.query.filter(User.group.has(Group.key == "user"))

        data = {
            'Nữ': users.filter(User.gender is False).count(),
            'Nam': users.filter(User.gender is True).count(),
            'Tổng': users.count()
        }

        return send_result(data=data, message="Thành công")
    except Exception as ex:
        return send_error(message=str(ex), code=442)



