from flask import Blueprint
from sqlalchemy import asc
from app.api.helper import send_result, send_error
from app.models import Region
from app.validator import ShipperSchema

api = Blueprint('manage/region', __name__)

@api.route("", methods=["GET"])
def get_region():
    try:

        query =  Region.query.filter().order_by(asc(Region.id)).all()
        regions = ShipperSchema(many=True).dump(query)

        return send_result(data=regions)
    except Exception as ex:
        return send_error(message=str(ex))
