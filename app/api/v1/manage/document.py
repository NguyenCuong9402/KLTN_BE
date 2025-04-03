
from shortuuid import uuid
from flask import Blueprint, request
from sqlalchemy import desc, asc

from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.helper import send_result, send_error
from app.extensions import db
from app.models import User, DocumentStorage, Files, StaffDocumentFile

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


@api.route("<document_id>", methods=["POST"])
@jwt_required
def post_item(document_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()

        # Kiểm tra xem người dùng có tồn tại hay không
        if user is None:
            return send_error(message='Tài khoản không tồn tại')

        body = request.get_json()

        # Kiểm tra xem có 'list_id' trong dữ liệu gửi lên hay không
        list_id = body.get('list_id')
        if not list_id:
            return send_error(message='Danh sách ID tệp không được cung cấp')

        list_add_document = []

        # Duyệt qua danh sách tệp và tạo các bản ghi StaffDocumentFile
        for index, file_id in enumerate(list_id):
            document = StaffDocumentFile(
                id=str(uuid()),
                user_id=user_id,
                document_id=document_id,
                file_id=file_id,
                index=index
            )
            list_add_document.append(document)  # Thêm vào danh sách

        # Lưu tất cả các tài liệu vào cơ sở dữ liệu
        db.session.bulk_save_objects(list_add_document)
        db.session.commit()

        # Chuẩn bị dữ liệu trả về
        data = DocumentSchema(many=True).dump(list_add_document)
        return send_result(data=data)

    except Exception as ex:
        return send_error(message=str(ex))

