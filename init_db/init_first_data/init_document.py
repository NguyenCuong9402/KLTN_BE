import json
import os
import shortuuid

import pandas as pd
from flask import Flask

from app.models import Group, DocumentStorage
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

    def init_DocumentStorage(self):
        list_documents = [
            'Ảnh',
            'CMND/CCCD',
            'Đơn Xin Việc',
            'Bằng Cấp',
            'Giấy Khai Sinh',
            'Sơ Yếu Lý Lịch',
            'Giấy Khám Sức Khỏe',
            'Sổ BHXH',
        ]

        list_add_DocumentStorage= []
        for index, item in enumerate(list_documents):
            document = DocumentStorage(
                id=str(shortuuid.uuid()), name=item, index=index
            )
            list_add_DocumentStorage.append(document)
        db.session.bulk_save_objects(list_add_DocumentStorage)
        db.session.commit()

    def delete_DocumentStorage(self):
        DocumentStorage.query.filter().delete()
        db.session.commit()


if __name__ == '__main__':
    print("=" * 10, f"Starting init DocumentStorage to the database on the uri: {CONFIG.SQLALCHEMY_DATABASE_URI}", "=" * 10)
    worker = Worker()
    worker.delete_DocumentStorage()
    worker.init_DocumentStorage()
    print("=" * 50, "Add address Success", "=" * 50)

