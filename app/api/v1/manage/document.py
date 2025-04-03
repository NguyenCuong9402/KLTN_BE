
from shortuuid import uuid
from flask import Blueprint, request
from sqlalchemy import desc, asc

from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.helper import send_result, send_error
from app.models import User, DocumentStorage

from app.validator import DocumentSchema

api = Blueprint('manage/document', __name__)



@api.route("", methods=["GET"])
@jwt_required
def get_item():
    try:
        documents = DocumentStorage.query.filter().order_by(asc(DocumentStorage.index)).all()
        data = DocumentSchema(many=True).dump(documents)
        return send_result(data=data)
    except Exception as ex:
        return send_error(message=str(ex))

