import json
import os
import shortuuid

import pandas as pd
from flask import Flask

from app.models import Group, Community
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

    def init_community(self):
        list_community = [{
                'name': 'Review sản phẩm',
                'description': 'Nhóm review sản phảm',
            },
            {
                'name': 'Sản phẩm mới',
                'description': 'Nhóm đăng bài sản phẩm mới',
            },
            {
                'name': 'Góc tham khảo',
                'description': 'Dành cho người dùng tham khảo thời trang mới',
            },
            {
                'name': 'Góc chia sẻ',
                'description': 'Dành cho stylist chia sẻ thời trang mới',
            },

        ]
        list_add_community= []
        for item in list_community:
            community = Community(
                id=str(shortuuid.uuid()), **item
            )
            list_add_community.append(community)
        db.session.bulk_save_objects(list_add_community)
        db.session.commit()

    def delete_community(self):
        Community.query.filter().delete()
        db.session.commit()


if __name__ == '__main__':
    print("=" * 10, f"Starting init Community to the database on the uri: {CONFIG.SQLALCHEMY_DATABASE_URI}", "=" * 10)
    worker = Worker()
    worker.delete_community()
    worker.init_community()
    print("=" * 50, "Add address Success", "=" * 50)
