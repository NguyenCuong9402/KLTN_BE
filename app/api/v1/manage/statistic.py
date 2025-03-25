import json

from flask import Blueprint, request, make_response, send_file, Response
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError
from sqlalchemy import asc, desc

from sqlalchemy_pagination import paginate

from app.api.helper import send_result, send_error
from app.enums import KEY_GROUP_NOT_STAFF
from app.extensions import logger
from app.models import Group, TypeProduct, Product, Shipper, Orders, User, Article
from app.utils import trim_dict, escape_wildcard
from app.validator import GroupSchema, QueryParamsAllSchema

api = Blueprint('statistic', __name__)


@api.route('/product_by_type', methods=['GET'])
@jwt_required
def get_number_product_by_type():
    try:

        data = [
            {
                "name": p.name,
                "total": Product.query.filter(
                    Product.type_product_id.in_([p.id] + [child.id for child in p.type_child])
                ).count()
            }
            for p in TypeProduct.query.filter(TypeProduct.type_id.is_(None)).order_by(asc(TypeProduct.key)).all()
        ]

        total_all = sum(item["total"] for item in data)

        data_statistic = {}

        total_percent = 0  # Tổng phần trăm đã tính trước mục cuối

        for index, item in enumerate(data):
            if total_all == 0:
                phan_tram = 0  # Tránh chia cho 0
            else:
                phan_tram = (item['total'] / total_all) * 100

            if index == len(data) - 1 and phan_tram > 0:
                data_statistic[item['name']] = 100 - total_percent  # Điều chỉnh mục cuối cùng
            else:
                data_statistic[item['name']] = round(phan_tram, 2)
                total_percent += data_statistic[item['name']]

        return send_result(data={'result': data_statistic, 'data_count': data }, message="Thành công")
    except Exception as ex:
        return send_error(message=str(ex), code=442)


@api.route('', methods=['GET'])
@jwt_required
def statistic_all():
    try:
        data = {
            'user': User.query.filter(User.group.has(Group.key == "user")).count(),
            'shipper': Shipper.query.filter().count(),
            'product': Product.query.filter().count(),
            'orders': Orders.query.filter().count(),
            'article': Article.query.filter().count(),
            'staff': User.query.filter(User.group.has(Group.is_staff == True)).count(),
        }

        return send_result(data=data, message="Thành công")
    except Exception as ex:
        return send_error(message=str(ex), code=442)



