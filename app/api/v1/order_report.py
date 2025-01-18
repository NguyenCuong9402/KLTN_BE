from shortuuid import uuid
from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy import desc, asc
from sqlalchemy_pagination import paginate

from app.enums import TYPE_FILE_LINK
from app.extensions import db

from app.api.helper import send_result, send_error
from app.models import FileLink, OrderReport, User
from app.utils import trim_dict, get_timestamp_now, escape_wildcard
from app.validator import ReportValidation, OrderReportSchema, QueryParamsOrderSchema
from flask_jwt_extended import get_jwt_identity, jwt_required

api = Blueprint('order_report', __name__)

@api.route('/new', methods=['POST'])
@jwt_required
def new():
    try:
        user_id = get_jwt_identity()
        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = ReportValidation()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')

        files = json_body.pop('files')
        json_body['user_id'] = user_id
        order_report = OrderReport(**json_body, id=str(uuid()))
        db.session.add(order_report)
        db.session.flush()

        file_objects = [FileLink(id=str(uuid()), table_id=order_report.id, file_id=file["file_id"],
                                 table_type=TYPE_FILE_LINK.get('ORDER_REPORT', 'order_report'),
                                 index=index, created_date=get_timestamp_now()+index)
                        for index, file in enumerate(files)]
        db.session.bulk_save_objects(file_objects)
        db.session.flush()

        db.session.commit()
        return send_result(message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


@api.route("/<report_id>", methods=["GET"])
@jwt_required
def get_item(report_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Người dùng không tồn tại.')
        item = OrderReport.query.filter(OrderReport.id == report_id, OrderReport.user_id==user_id).first()
        if item is None:
            return send_error(message="Đơn khiếu nại không tồn tại, F5 lại web")
        data = OrderReportSchema().dump(item)
        return send_result(data=data)
    except Exception as ex:
        return send_error(message=str(ex))

@api.route("", methods=["GET"])
@jwt_required
def get_items():
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Người dùng không tồn tại.')
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

        query = OrderReport.query.filter(OrderReport.user_id==user_id)

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