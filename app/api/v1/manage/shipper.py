import json
from shortuuid import uuid
from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy import desc, asc, or_
from sqlalchemy_pagination import paginate

from app.extensions import db
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.api.helper import send_result, send_error
from app.models import Shipper, PriceShip
from app.utils import trim_dict, escape_wildcard, get_timestamp_now
from app.validator import ProductValidation, QueryParamsAllSchema, ShipperSchema, ShipperValidation

api = Blueprint('manage/shipper', __name__)


@api.route('', methods=['POST'])
@jwt_required
def new():
    try:
        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = ShipperValidation()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')
        name = json_body.pop('name')
        count = Shipper.query.count()
        shipper = Shipper(id=str(uuid()), name=name, index=count)

        db.session.add(shipper)
        db.session.flush()
        list_ship_prices= []
        for region_id, price in json_body.items():
            price_ship = PriceShip(
                id=str(uuid()), price=price,
                region_id=region_id, shipper_id=shipper.id
            )
            list_ship_prices.append(price_ship)
        db.session.bulk_save_objects(list_ship_prices)
        db.session.commit()
        return send_result(message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


@api.route("/<ship_id>", methods=["DELETE"])
@jwt_required
def remove_item(ship_id):
    try:
        Shipper.query.filter(Shipper.id == ship_id).update({"is_delete": True}, synchronize_session=False)

        db.session.flush()
        db.session.commit()
        return send_result(message="Xóa sản phẩm thành công")
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))


@api.route("/<ship_id>", methods=["PUT"])
@jwt_required
def update_item(ship_id):
    try:

        shipper = Shipper.query.filter(Shipper.id == ship_id).first()

        if shipper is None:
            return send_error(message='Đơn vị vận chuyển không tồn tại.')

        db.session.flush()
        db.session.commit()
        return send_result(message="Cập nhật thành công.")
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))


@api.route("", methods=["GET"])
def get_shipper():
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

        query = Shipper.query.filter(Shipper.is_delete.is_(False))

        if text_search:
            text_search = text_search.strip()
            text_search = text_search.lower()
            text_search = escape_wildcard(text_search)
            text_search = "%{}%".format(text_search)

            query = query.filter(Shipper.name.ilike(f"%{text_search}%"))

        column_sorted = getattr(Shipper, order_by)

        query = query.order_by(desc(column_sorted)) if sort == "desc" else query.order_by(asc(column_sorted))

        paginator = paginate(query, page, page_size)

        shippers = ShipperSchema(many=True).dump(paginator.items)

        response_data = dict(
            items=shippers,
            total_pages=paginator.pages if paginator.pages > 0 else 1,
            total=paginator.total,
            has_previous=paginator.has_previous,
            has_next=paginator.has_next
        )
        return send_result(data=response_data)
    except Exception as ex:
        return send_error(message=str(ex))
