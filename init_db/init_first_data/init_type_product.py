import json
import os
import shortuuid

import pandas as pd
from flask import Flask

from app.models import Group, TypeProduct
from app.extensions import db
from app.settings import DevConfig

CONFIG = DevConfig


class Worker:
    def __init__(self):
        app = Flask(__name__)
        app.config.from_object(CONFIG)
        db.app = app
        db.init_app(app)
        app_context = app.app_context()
        app_context.push()

    def init_type(self):
        list_type = [
            {
                'key': 'ao',
                'name': 'Áo',
                'child_type': [
                    {'key': 'ao_khoac', 'name': 'Áo Khoác'},
                    {'key': 'ao_bo', 'name': 'Áo Bò'},
                    {'key': 'ao_thun', 'name': 'Áo Thun'},
                    {'key': 'ao_so_mi', 'name': 'Áo Sơ Mi'},
                ]
            },
            {
                'key': 'quan',
                'name': 'Quần',
                'child_type': [
                    {'key': 'quan_jeans', 'name': 'Quần Jeans'},
                    {'key': 'quan_tay', 'name': 'Quần Tây'},
                    {'key': 'quan_kaki', 'name': 'Quần Kaki'},
                    {'key': 'quan_shorts', 'name': 'Quần Shorts'},
                ]
            },
            {
                'key': 'phukien',
                'name': 'Phụ Kiện',
                'child_type': [
                    {'key': 'that_lung', 'name': 'Thắt Lưng'},
                    {'key': 'kinh_mat', 'name': 'Kính Mát'},
                    {'key': 'non', 'name': 'Nón'},
                    {'key': 'vi_da', 'name': 'Ví Da'},
                ]
            },
        ]

        list_add_type = []
        for item in list_type:
            parent_type = TypeProduct(
                id=str(shortuuid.uuid()),
                key=item['key'],
                name=item['name'],
                type_id=None  # Đây là sản phẩm cha
            )
            list_add_type.append(parent_type)
            db.session.add(parent_type)
            db.session.flush()  # Lấy ID của parent ngay sau khi thêm vào DB

            # Thêm child types
            for child in item.get('child_type', []):
                child_type = TypeProduct(
                    id=str(shortuuid.uuid()),
                    key=child['key'],
                    name=child['name'],
                    type_id=parent_type.id  # Liên kết với sản phẩm cha
                )
                list_add_type.append(child_type)

        db.session.bulk_save_objects(list_add_type)
        db.session.commit()

    def delete_type(self):
        TypeProduct.query.filter().delete()
        db.session.commit()


if __name__ == '__main__':
    print("=" * 10, f"Starting init Address to the database on the uri: {CONFIG.SQLALCHEMY_DATABASE_URI}", "=" * 10)
    worker = Worker()
    worker.delete_type()
    worker.init_type()
    print("=" * 50, "Add address Success", "=" * 50)
