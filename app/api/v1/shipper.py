
from flask import Blueprint
from sqlalchemy import asc

from app.api.helper import send_error, send_result, Token
from app.models import Shipper

from app.validator import ShipperSchema

api = Blueprint('shipper', __name__)

@api.route("", methods=["GET"])
def get_shipper():
    try:
        shipper = Shipper.query.filter(Shipper.is_delete.is_(False)).order_by(asc(Shipper.index)).all()

        if len(shipper) == 0:
            return send_error(message='Không có đơn vị vận chuyển nào.')

        data = ShipperSchema(many=True).dump(shipper)
        return send_result(message='Done', data=data)
    except Exception as ex:
        return send_error(message=str(ex))





