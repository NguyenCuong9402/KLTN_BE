import json
from collections import defaultdict
from datetime import datetime, timezone
from sqlalchemy import cast, Integer, BigInteger

from dateutil.relativedelta import relativedelta
from flask import Blueprint, request, make_response, send_file, Response
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError
from sqlalchemy import asc, desc, func

from sqlalchemy_pagination import paginate

from app.api.helper import send_result, send_error
from app.enums import KEY_GROUP_NOT_STAFF, STATUS_ORDER
from app.extensions import logger, db
from app.models import Group, TypeProduct, Product, Shipper, Orders, User, Article, OrderItems
from app.utils import trim_dict, escape_wildcard
from app.validator import GroupSchema, QueryParamsAllSchema

api = Blueprint('statistic', __name__)


@api.route('/number_product_by_type', methods=['GET'])
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

        return send_result(data={'result': data_statistic, 'data_count': data}, message="Thành công")
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


@api.route('/revenue_and_sold_product_by_type', methods=['GET'])
@jwt_required
def get_number_by_type_product_6_month_ago():
    try:
        month = request.args.get('month', 12, type=int)

        now_dt = datetime.now(timezone.utc).replace(day=1)

        # Tạo danh sách 10 tháng gần nhất
        months = [(now_dt - relativedelta(months=i)).strftime("%m-%Y") for i in range(month)][::-1]

        # Lấy danh sách các loại sản phẩm
        type_products = TypeProduct.query.filter(TypeProduct.type_id.is_(None)).order_by(asc(TypeProduct.key)).all()
        type_product_dict = {
            p.id: {"name": p.name, "list_id": [p.id] + [child.id for child in p.type_child]} for p in type_products
        }

        # Truy vấn dữ liệu từ OrderItems
        query = (
            db.session.query(
                func.date_format(func.from_unixtime(OrderItems.created_date), "%m-%Y").label("month"),
                Product.type_product_id,
                cast(func.sum(OrderItems.quantity), Integer).label("total_quantity"),
                cast(func.sum(OrderItems.count), BigInteger).label("total_count")

            )
            .join(Product, OrderItems.product_id == Product.id)
            .join(Orders, OrderItems.order_id == Orders.id)
            .filter(
                (Orders.payment_status == True) & (Orders.payment_online_id.isnot(None)) |
                (Orders.status == STATUS_ORDER.get("RESOLVED"))
            )
            .filter(OrderItems.created_date >= int((now_dt - relativedelta(months=month-1)).timestamp()))
            .group_by("month", Product.type_product_id)
            .order_by("month")
        )

        # Xử lý dữ liệu
        sales_data = defaultdict(lambda: defaultdict(lambda: {"quantity": 0, "count": 0}))

        for row in query:
            month = row.month
            type_id = row.type_product_id
            quantity = row.total_quantity
            count = row.total_count

            # Gán dữ liệu vào danh sách tương ứng
            for type_key, type_value in type_product_dict.items():
                if type_id in type_value["list_id"]:
                    sales_data[type_value["name"]][month]["quantity"] += quantity
                    sales_data[type_value["name"]][month]["count"] += count

        # Chuyển đổi thành format JSON
        series_sold = [
            {
                "name": type_name,
                "data": [sales_data[type_name][month]["quantity"] for month in months],  # Lấy số lượng
            }
            for type_name in sales_data
        ]

        series_revue = [
            {
                "name": type_name,
                "data": [sales_data[type_name][month]["count"] for month in months],  # Lấy số lần bán (revue)
            }
            for type_name in sales_data
        ]

        # Kết quả JSON
        chart_data_sold = {
            "categories": months,
            "series": series_sold
        }

        chart_data_revenue = {
            "categories": months,
            "series": series_revue
        }

        return send_result(data={
            'chart_data_sold': chart_data_sold,
            'chart_data_revenue': chart_data_revenue,
            'month': month
        }, message="Thành công")

    except Exception as ex:
        return send_error(message=str(ex), code=442)
