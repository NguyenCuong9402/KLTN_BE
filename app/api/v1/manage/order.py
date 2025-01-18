from shortuuid import uuid
from flask import Blueprint
from app.extensions import db
from flask_jwt_extended import jwt_required
from app.api.helper import send_result, send_error
from app.models import Orders

api = Blueprint('manage/order', __name__)


@api.route('/change-status/<order_id>/<status>', methods=['PUT'])
@jwt_required
def change_status(order_id, status):
    try:

        order = Orders.query.filter_by(id=order_id).first()
        order.status = status
        db.session.flush()

        db.session.commit()
        return send_result(message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)
