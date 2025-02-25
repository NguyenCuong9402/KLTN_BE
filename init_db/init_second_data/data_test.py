import json
import os
from shortuuid import uuid
import random
import pandas as pd
from flask import Flask
from sqlalchemy.sql.expression import func

from app.enums import TYPE_FILE_LINK
from app.models import Product, Size, Color, FileLink, TypeProduct
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

    def add_db_product(self):
        ### Hướng dâẫn tạo data test. Upload file từ màn create,
        # xong thay data file đc trả ra từ api vô. Xong chạy file này là oke
        data = {
            "name": "Áo phông",
            "describe": "Áo đẹp giá tốt",
            "discount_from_date": 1735365861,
            "discount_to_date": 1735521538,
            "sizes": [
                "S",
                "M",
                "L",
                "XL"
            ],
            "colors": [
                "Xanh",
                "Trắng"
            ],
            "files": [
                {
                    "file_id": "Z5CZYy3TxG8zYJqUEKW6Cq",
                    "file_path": "/files/Z5CZYy3TxG8zYJqUEKW6Cq.jpg"
                },
                {
                    "file_id": "7kqVDEec6f5kLcajSMKoZd",
                    "file_path": "/files/7kqVDEec6f5kLcajSMKoZd.jpg"
                }
            ]
        }

        values = [200000, 250000, 300000, 350000, 400000]

        files = data.pop('files')
        sizes = data.pop('sizes')
        colors = data.pop('colors')
        name = data.pop('name')

        random_type = TypeProduct.query.filter(TypeProduct.type_id.isnot(None)).order_by(func.random()).first()

        if random_type:
            for i in range(1, 40):
                product = Product(**data, type_product_id=random_type.id, id=str(uuid()), original_price=random.choice(values),
                                  name=f'Sản phẩm {name} {i}', discount=random.randint(1, 20),
                                  created_date=get_timestamp_now() + i)
                db.session.add(product)
                db.session.flush()

                size_objects = [Size(id=str(uuid()), name=size, product_id=product.id, index=index,
                                     created_date=get_timestamp_now() + index) for index, size in enumerate(sizes)]
                color_objects = [Color(id=str(uuid()), name=color, product_id=product.id, index=index,
                                       created_date=get_timestamp_now() + index) for index, color in enumerate(colors)]
                db.session.bulk_save_objects(size_objects)
                db.session.bulk_save_objects(color_objects)
                db.session.flush()

                file_objects = [FileLink(id=str(uuid()), table_id=product.id, file_id=file["file_id"], table_type = TYPE_FILE_LINK.get('PRODUCT', 'product'),
                                                index=index, created_date=get_timestamp_now() + index)
                                for index, file in enumerate(files)]
                db.session.bulk_save_objects(file_objects)
                db.session.flush()
                db.session.commit()


if __name__ == '__main__':
    print("=" * 10, f"Starting init Address to the database on the uri: {CONFIG.SQLALCHEMY_DATABASE_URI}", "=" * 10)
    worker = Worker()
    worker.add_db_product()
    print("=" * 50, "Add address Success", "=" * 50)
