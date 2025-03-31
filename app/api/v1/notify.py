import json
import os
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError
from sqlalchemy import asc, desc, exists

from sqlalchemy_pagination import paginate

from app.api.helper import send_result, send_error
from app.enums import STATUS_ORDER
from app.models import db, Product, User, Orders, Notify, NotifyDetail
from app.utils import escape_wildcard
from app.validator import OrderSchema, QueryParamsOrderSchema, NotifySchema, QueryNotifyParamsSchema

api = Blueprint('notify', __name__)

@api.route("/<notify_id>", methods=["GET"])
@jwt_required
def get_item(notify_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Người dùng không tồn tại.')
        item = Notify.query.filter(Notify.id == notify_id, Orders.user_id==user_id).first()
        if item is None:
            return send_error(message="Thông báo không tồn tại, F5 lại web")
        if Notify.unread:
            Notify.unread = False
            db.session.flush()
            db.session.commit()
        data = NotifySchema().dump(item)
        return send_result(data=data)
    except Exception as ex:
        db.session.flush()
        return send_error(message=str(ex))

@api.route("/number_unread", methods=["GET"])
@jwt_required
def number_unread():
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message='Người dùng không tồn tại.')

        query = Notify.query.filter(Notify.user_id == user_id,
                                    db.session.query(exists().where(NotifyDetail.notify_id == Notify.id)).scalar_subquery())

        if user.last_seen_notify:
            query = query.filter(Notify.modified_date > user.last_seen_notify)

        return send_result(data={'number_new_notify': query.count()})

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
            params = QueryNotifyParamsSchema().load(params) if params else dict()
        except ValidationError as err:
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)
        notify_unread = params.get('notify_unread')
        page = params.get('page', 1)
        page_size = params.get('page_size', 10)

        query = Notify.query.filter(Notify.user_id==user_id,
                                    db.session.query(exists().where(NotifyDetail.notify_id == Notify.id)).scalar_subquery())

        if notify_unread:
            query = query.filter(Notify.unread.is_(True))

        query = query.order_by(desc(Notify.modified_date))

        paginator = paginate(query, page, page_size)

        notify_data = NotifySchema(many=True).dump(paginator.items)

        response_data = dict(
            items=notify_data,
            total_pages=paginator.pages if paginator.pages > 0 else 1,
            total=paginator.total,
            has_previous=paginator.has_previous,
            has_next=paginator.has_next
        )
        return send_result(data=response_data)
    except Exception as ex:
        return send_error(message=str(ex))

