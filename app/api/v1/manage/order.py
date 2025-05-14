from datetime import timedelta

from dateutil.relativedelta import relativedelta
from marshmallow import ValidationError
from flask import Blueprint, request
from sqlalchemy import desc, asc, or_
from sqlalchemy_pagination import paginate

from app.enums import STATUS_ORDER
from app.extensions import db
from flask_jwt_extended import get_jwt_identity
from app.api.helper import send_result, send_error
from app.gateway import authorization_require
from app.models import Orders, User
from app.signal import handle_ship_orders_notification
from app.utils import escape_wildcard, get_timestamp_now, get_datetime_now
from app.validator import OrderSchema, QueryParamsManageOrderSchema

api = Blueprint('manage/order', __name__)


@api.route('/<order_id>', methods=['PUT'])
@authorization_require()
def change_status(order_id):
    try:
        body_request = request.get_json()

        status = body_request.get('status', None)

        order = Orders.query.filter_by(id=order_id).first()
        if order is None:
            return send_error(message='Đơn hàng không tồn tại')

        if status not in list(STATUS_ORDER.values()):
            return send_error(message='Status không đúng')

        if status == STATUS_ORDER['DELIVERING']:
            order.modified_date = get_timestamp_now()

        order.status = status
        db.session.flush()
        db.session.commit()
        data = OrderSchema().dump(order)
        if status == STATUS_ORDER['DELIVERING']:
            try:
                handle_ship_orders_notification(order)
            except:
                pass
        return send_result(data=data, message="Cập nhật thành công")
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)



@api.route("/<order_id>", methods=["GET"])
@authorization_require()
def get_item(order_id):
    try:
        user_id = get_jwt_identity()
        item = Orders.query.filter(Orders.id == order_id).first()
        if item is None:
            return send_error(message="Đơn hàng không tồn tại, F5 lại web")
        data = OrderSchema().dump(item)
        return send_result(data=data)
    except Exception as ex:
        return send_error(message=str(ex))

@api.route("", methods=["GET"])
@authorization_require()
def get_items():
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = QueryParamsManageOrderSchema().load(params) if params else dict()
        except ValidationError as err:
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)
        page = params.get('page', 1)
        page_size = params.get('page_size', 10)
        order_by = params.get('order_by', 'created_date')
        sort = params.get('sort', 'desc')
        status = params.get('status', None)
        text_search = params.get('text_search', None)

        time = params.get('time', None)

        query = Orders.query.filter()
        if status:
            query = query.filter(Orders.status==status)

        # Tính toán timestamp cho khoảng thời gian lọc
        if time:
            datetime_now = get_datetime_now()
            if time == 'week':
                time_filter = int((datetime_now - timedelta(weeks=1)).timestamp())
            elif time == 'month':
                time_filter = int((datetime_now - relativedelta(months=1)).timestamp())
            elif time == 'year':
                time_filter = int((datetime_now - relativedelta(years=1)).timestamp())
            else:
                time_filter = None

            # Lọc theo created_date nếu có thời gian hợp lệ
            if time_filter:
                query = query.filter(Orders.created_date >= time_filter)

        if text_search:
            text_search = text_search.strip()
            text_search = text_search.lower()
            text_search = escape_wildcard(text_search)
            text_search = "%{}%".format(text_search)
            query = query.join(User).filter(
                or_(
                    Orders.id.ilike(text_search),
                    User.email.ilike(text_search)
                )
            )

        column_sorted = getattr(Orders, order_by)

        query = query.order_by(desc(column_sorted)) if sort == "desc" else query.order_by(asc(column_sorted))

        paginator = paginate(query, page, page_size)

        orders = OrderSchema(many=True).dump(paginator.items)

        response_data = dict(
            items=orders,
            total_pages=paginator.pages if paginator.pages > 0 else 1,
            total=paginator.total,
            has_previous=paginator.has_previous,
            has_next=paginator.has_next
        )
        return send_result(data=response_data)
    except Exception as ex:
        return send_error(message=str(ex))
