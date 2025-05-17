import json
import os
import shutil

from shortuuid import uuid
import random
import pandas as pd
from flask import Flask
from sqlalchemy.sql.expression import func

from app.enums import TYPE_FILE_LINK
from app.models import Product, Size, Color, FileLink, TypeProduct, Files
from app.extensions import db
from app.settings import DevConfig
from app.utils import get_timestamp_now

CONFIG = DevConfig


class Worker:
    def __init__(self):
        app = Flask(__name__)
        app.config.from_object(CONFIG)
        db.app = app
        db.init_app(app)
        app_context = app.app_context()
        app_context.push()

    def init_file_product(self):
        Files.query.filter().delete()
        Product.query.filter().delete()
        db.session.commit()

    def add_db_product(self):
        ### Hướng dâẫn tạo data test. Upload file từ màn create,
        # xong thay data file đc trả ra từ api vô. Xong chạy file này là oke

        FOLDER_SRC = r"E:/KTLN/BE/app/file_mau/"  # Thư mục nguồn
        FOLDER_DEST = r"E:/KTLN/BE/app/files/image"  # Thư mục đích

        # FOLDER_SRC = r"C:\Users\Administrator\Documents\KhoaLuanTotNghiep\kltn-be\app\file_mau"
        # FOLDER_DEST = r"C:\Users\Administrator\Documents\KhoaLuanTotNghiep\kltn-be\app\files\image/"

        # FOLDER_SRC = r"E:\KLTN\kltn-be\app\file_mau"
        # FOLDER_DEST = r"E:\KLTN\kltn-be\app\files\image/"

        FOLDER_DEST_SAVE_DB = "/files/image/"

        if not os.path.exists(FOLDER_DEST):
            os.makedirs(FOLDER_DEST)

        if not os.path.exists(FOLDER_SRC):
            print('Thư mục không tồn tại')
            return "Thư mục không tồn tại"

        result = []

        for file_name in os.listdir(FOLDER_SRC):
            file_id, file_extension = os.path.splitext(file_name)  # Lấy tên file & đuôi file

            # Kiểm tra file đã tồn tại trong DB chưa
            existing_file = Files.query.filter_by(id=file_id).first()
            if not existing_file:
                # Tạo UUID mới làm tên file an toàn
                new_file_path = os.path.join(FOLDER_DEST, file_name)

                # Copy file từ `file_mau` sang `app/files/`
                shutil.copy(os.path.join(FOLDER_SRC, file_name), new_file_path)

                # Lưu vào DB
                new_file = Files(
                    id=file_id,
                    file_path=FOLDER_DEST_SAVE_DB + file_name,
                    created_date=get_timestamp_now()
                )
                db.session.add(new_file)

                # Thêm vào danh sách kết quả
                result.append({"id": file_id, "file_path": new_file_path})

        db.session.commit()

        data = {
            "describe": "Đẹp, chất lượng cao, giá tốt",
            "sizes": [
                "M",
                "L",
                "XL",
                "XXL"
            ],
            "colors": [
                "Đen",
                "Trắng",
                "Xanh",

            ],
            "files": result
        }

        values = [200000, 250000, 300000, 350000, 400000, 100000, 150000]

        files = data.pop('files')
        sizes = data.pop('sizes')
        colors = data.pop('colors')

        type_datas = TypeProduct.query.filter(TypeProduct.type_id.isnot(None)).all()

        for type_data in type_datas:
            for i in range(1, 3):
                product = Product(**data, type_product_id=type_data.id, id=str(uuid()), original_price=random.choice(values),
                                  name=f'{type_data.name} {i}', discount=random.randint(1, 20),
                                  created_date=get_timestamp_now() + i)
                db.session.add(product)
                db.session.flush()

                if type_data.parent and type_data.parent.key == 'phu_kien':
                    size_list = ['FreeSize']
                else:
                    size_list = sizes

                size_objects = [
                    Size(
                        id=str(uuid()),
                        name=size,
                        product_id=product.id,
                        index=index,
                        created_date=get_timestamp_now() + index
                    )
                    for index, size in enumerate(size_list)
                ]
                color_objects = [Color(id=str(uuid()), name=color, product_id=product.id, index=index,
                                       created_date=get_timestamp_now() + index) for index, color in enumerate(colors)]
                db.session.bulk_save_objects(size_objects)
                db.session.bulk_save_objects(color_objects)
                db.session.flush()

                file_objects = [FileLink(id=str(uuid()), table_id=product.id, file_id=file["id"], table_type = TYPE_FILE_LINK.get('PRODUCT', 'product'),
                                                index=index, created_date=get_timestamp_now() + index)
                                for index, file in enumerate(files)]
                db.session.bulk_save_objects(file_objects)
                db.session.flush()
        db.session.commit()


if __name__ == '__main__':
    print("=" * 10, f"Starting init Address to the database on the uri: {CONFIG.SQLALCHEMY_DATABASE_URI}", "=" * 10)
    worker = Worker()
    worker.init_file_product()
    worker.add_db_product()
    print("=" * 50, "Add address Success", "=" * 50)
