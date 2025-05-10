from shortuuid import uuid
from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy import desc, asc
from sqlalchemy_pagination import paginate

from app.enums import TYPE_FILE_LINK, REPORT_ORDER_TYPE
from app.extensions import db

from app.api.helper import send_result, send_error
from app.gateway import authorization_require
from app.models import FileLink, OrderReport, User
from app.utils import trim_dict, get_timestamp_now, escape_wildcard
from app.validator import ReportValidation, OrderReportSchema, QueryParamsOrderSchema
from flask_jwt_extended import get_jwt_identity, jwt_required

api = Blueprint('report', __name__)

@api.route("/<report_id>", methods=["GET"])
@authorization_require()
def get_item(report_id):
    try:
        item = OrderReport.query.filter(OrderReport.id == report_id).first()
        if item is None:
            return send_error(message="Đơn khiếu nại không tồn tại, F5 lại web")
        data = OrderReportSchema().dump(item)
        return send_result(data=data)
    except Exception as ex:
        return send_error(message=str(ex))


@api.route("/<report_id>", methods=["PUT"])
@authorization_require()
def put_item(report_id):
    try:
        item = OrderReport.query.filter(OrderReport.id == report_id).first()
        if item is None:
            return send_error(message="Đơn khiếu nại không tồn tại, F5 lại web")

        body_request = request.get_json()

        result = body_request.get("result", "")
        if not result.strip():
            return send_error(message='Không để trống phản hồi')
        item.result = result.strip()
        item.status = REPORT_ORDER_TYPE['RESOLVED']
        db.session.flush()
        db.session.commit()
        data = OrderReportSchema().dump(item)
        return send_result(data=data, message="ok")
    except Exception as ex:
        return send_error(message=str(ex))

@api.route("", methods=["GET"])
@authorization_require()
def get_items():
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = QueryParamsOrderSchema().load(params) if params else dict()
        except ValidationError as err:
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)
        page = params.get('page', 1)
        page_size = params.get('page_size', 10)
        order_by = params.get('order_by', 'created_date')
        sort = params.get('sort', 'desc')
        status = params.get('status', None)
        text_search = params.get('text_search', None)

        query = OrderReport.query.filter()

        if status:
            query = query.filter(OrderReport.status==status)

        if text_search:
            text_search = text_search.strip()
            text_search = text_search.lower()
            text_search = escape_wildcard(text_search)
            text_search = "%{}%".format(text_search)
            query = query.filter(OrderReport.id.ilike(text_search))

        column_sorted = getattr(OrderReport, order_by)

        query = query.order_by(desc(column_sorted)) if sort == "desc" else query.order_by(asc(column_sorted))

        paginator = paginate(query, page, page_size)

        report_orders = OrderReportSchema(many=True).dump(paginator.items)

        response_data = dict(
            items=report_orders,
            total_pages=paginator.pages if paginator.pages > 0 else 1,
            total=paginator.total,
            has_previous=paginator.has_previous,
            has_next=paginator.has_next
        )
        return send_result(data=response_data)
    except Exception as ex:
        return send_error(message=str(ex))