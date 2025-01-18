import os
from shortuuid import uuid

from flask import Blueprint, request, make_response, send_file, Response
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import asc
from io import BytesIO
import datetime
import io

from werkzeug.utils import secure_filename

from app.api.helper import send_result, send_error
from app.models import db, Product, User, Orders, OrderItems, CartItems, Files

api = Blueprint('file', __name__)

FILE_ORIGIN = "app"

FOLDER = "/files/"

@api.route('upload_file', methods=['POST'])
def upload_file():
    try:
        # Lấy file từ request (chỉ lấy file đầu tiên từ input 'file')
        file = request.files.get('file')  # Chỉ nhận một file
        if not file:
            return send_error(message="No file provided")

        # Lấy tên file và phần mở rộng
        filename, file_extension = os.path.splitext(file.filename)

        # Tạo UUID làm tên file an toàn
        id_file = str(uuid())
        file_name = secure_filename(id_file) + file_extension

        if not os.path.exists(FILE_ORIGIN + FOLDER):
            os.makedirs(FILE_ORIGIN + FOLDER)
        file_path = FILE_ORIGIN + FOLDER + file_name
        file.save(os.path.join(file_path))
        file = Files(id=id_file, file_path=FOLDER + file_name)
        db.session.add(file)
        db.session.commit()
        dt = {
            "file_path": file.file_path,
            "file_id": file.id
        }

        return send_result(data=dt, message="File uploaded successfully")
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))



@api.route('upload', methods=['POST'])
def upload_picture():
    try:
        files = request.files.getlist('files')  # Nhận danh sách file từ 'files'
        if not files:
            return send_error(message="No files provided")

        # Tạo danh sách để lưu thông tin các file đã upload
        uploaded_files = []
        for file in files:
            try:
                filename, file_extension = os.path.splitext(file.filename)
                id_file = str(uuid())
                file_name = secure_filename(id_file) + file_extension
                if not os.path.exists(FILE_ORIGIN+FOLDER):
                    os.makedirs(FILE_ORIGIN+FOLDER)
                file_path = FILE_ORIGIN + FOLDER + file_name
                file.save(os.path.join(file_path))
                file = Files(id=id_file, file_path=FOLDER + file_name)
                db.session.add(file)
                db.session.commit()
            except Exception:
                continue
            dt = {
                "file_path": file.file_path,
                "file_id": file.id
            }
            uploaded_files.append(dt)

        return send_result(data=uploaded_files, message="Ok")
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))

@api.route('/<file_id>', methods=['GET'])
def get_picture(file_id):
    try:
        file = Files.query.filter(Files.id == file_id).first()
        if file is None:
            return send_error(message='File not found')
        file = os.path.abspath(file.file_path)
        return send_file(file, as_attachment=True)
    except Exception as ex:
        return send_error(message=str(ex))
