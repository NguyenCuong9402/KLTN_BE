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

    def init_group(self):
        list_type = [{
                'id': 'mt7kiahfSYXN6iANorjUcH',
                'key': 'ao',
                'name': 'Áo',

            },
            {   'id': 'mt7kiahfSYXN6iANorjUcd',
                'key': 'quan',
                'name': 'Quần',

            },
            {   'id': 'mt7kiahfSYXN6iANorjUce',
                'key': 'phukien',
                'name': 'Phụ Kiện',

            },
        ]
        list_add_type= []
        for item in list_type:
            type_product = TypeProduct(
                **item
            )
            list_add_type.append(type_product)
        db.session.bulk_save_objects(list_add_type)
        db.session.commit()

    def delete_type(self):
        TypeProduct.query.filter().delete()
        db.session.commit()


if __name__ == '__main__':
    print("=" * 10, f"Starting init Address to the database on the uri: {CONFIG.SQLALCHEMY_DATABASE_URI}", "=" * 10)
    worker = Worker()
    worker.delete_type()
    worker.init_group()
    print("=" * 50, "Add address Success", "=" * 50)
