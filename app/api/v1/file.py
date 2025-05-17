import os
from shortuuid import uuid

from flask import Blueprint, request, send_file

from werkzeug.utils import secure_filename

from app.api.helper import send_result, send_error
from app.models import db, Product, User, Orders, OrderItems, CartItems, Files

api = Blueprint('file', __name__)

FILE_ORIGIN = "app"

FOLDER = "/files/image_project/"

@api.route('upload_file', methods=['POST'])
def upload_one_file():
    try:
        # Lấy file từ request (chỉ lấy file đầu tiên từ input 'file')
        file = request.files.get('file')  # Chỉ nhận một file
        if not file:
            return send_error(message="No file provided")

        # Lấy tên file và phần mở rộng
        filename, file_extension = os.path.splitext(file.filename)
        file_extension = file_extension.lower()

        # Danh sách các định dạng hợp lệ
        allowed_extensions = ['.jpg', '.jpeg', '.png']

        if file_extension not in allowed_extensions:
            return send_error(message="Chỉ chấp nhận  định dạng JPG, JPEG, và PNG.")

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
            "id": file.id
        }

        return send_result(data=dt, message="File uploaded successfully")
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))



@api.route('upload', methods=['POST'])
def upload_multi_file():
    try:
        files = request.files.getlist('files')  # Nhận danh sách file từ 'files'
        if not files:
            return send_error(message="No files provided")
        allowed_extensions = ['.jpg', '.jpeg', '.png']

        # Tạo danh sách để lưu thông tin các file đã upload
        uploaded_files = []
        for file in files:
            try:
                filename, file_extension = os.path.splitext(file.filename)

                file_extension = file_extension.lower()

                if file_extension not in allowed_extensions:
                    continue

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
                "id": file.id
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
