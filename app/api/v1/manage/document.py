import os

from shortuuid import uuid
from flask import Blueprint, request
from sqlalchemy import desc, asc

from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app.api.helper import send_result, send_error
from app.api.v1.file import FILE_ORIGIN
from app.extensions import db
from app.models import User, DocumentStorage, Files, StaffDocumentFile

from app.validator import DocumentSchema, DocumentStaff

api = Blueprint('manage/document', __name__)

FOLDER = "/files/document/"


@api.route("", methods=["GET"])
@jwt_required
def danh_sach_document():
    try:
        documents = DocumentStorage.query.filter().order_by(asc(DocumentStorage.index)).all()
        data = DocumentSchema(many=True).dump(documents)
        return send_result(data=data)
    except Exception as ex:
        return send_error(message=str(ex))


@api.route("/<user_id>/<document_id>", methods=["GET"])
@jwt_required
def get_item(user_id, document_id):
    try:
        user = User.query.filter_by(id=user_id).first()

        # Kiểm tra xem người dùng có tồn tại hay không
        if user is None:
            return send_error(message='Tài khoản không tồn tại')

        document = (StaffDocumentFile.query.filter(StaffDocumentFile.document_id==document_id,
                                                  StaffDocumentFile.user_id == user_id)
                    .order_by(asc(StaffDocumentFile.created_date)).all())

        # Chuẩn bị dữ liệu trả về
        data = DocumentStaff(many=True).dump(document)
        return send_result(data=data)

    except Exception as ex:
        return send_error(message=str(ex))



@api.route('/<user_id>/upload/<document_id>', methods=['POST'])
@jwt_required
def upload_multi_file(user_id, document_id):
    try:
        user = User.query.filter_by(id=user_id).first()

        # Kiểm tra xem người dùng có tồn tại hay không
        if user is None:
            return send_error(message='Tài khoản không tồn tại')

        document = DocumentStorage.query.filter(DocumentStorage.id==document_id).first()

        # Kiểm tra xem người dùng có tồn tại hay không
        if document is None:
            return send_error(message='Mục tài liệu không tồn tại')

        files = request.files.getlist('files')  # Nhận danh sách file từ 'files'
        if not files:
            return send_error(message="No files provided")

        # Tạo danh sách để lưu thông tin các file đã upload
        data = []
        for file in files:
            try:
                filename, file_extension = os.path.splitext(file.filename)
                id_file = str(uuid())
                file_name = secure_filename(id_file) + file_extension
                if not os.path.exists(FILE_ORIGIN+FOLDER+f"{user_id}/"):
                    os.makedirs(FILE_ORIGIN+FOLDER+f"{user_id}/")
                file_path = FILE_ORIGIN + FOLDER +f"{user_id}/" + file_name
                file.save(os.path.join(file_path))
                file = Files(id=id_file, file_path= FOLDER +f"{user_id}/" + file_name)
                db.session.add(file)
                db.session.flush()
                document_staff = StaffDocumentFile(id=str(uuid()), document_id=document_id, user_id=user_id, file_id=file.id)
                db.session.add(document_staff)
                db.session.flush()
                db.session.commit()
                dt = DocumentStaff().dump(document_staff)
                data.append(dt)
            except Exception as ex:
                continue

        return send_result(data=data, message="Ok")
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))


@api.route("/<document_id>", methods=["DELETE"])
@jwt_required
def delete_item(document_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()

        # Kiểm tra xem người dùng có tồn tại hay không
        if user is None:
            return send_error(message='Tài khoản không tồn tại')

        StaffDocumentFile.query.filter(StaffDocumentFile.id == document_id).delete()
        db.session.commit()
        # Chuẩn bị dữ liệu trả về
        return send_result(message="Xóa thành công")

    except Exception as ex:
        return send_error(message=str(ex))
