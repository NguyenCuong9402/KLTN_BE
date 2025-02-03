import json
import os
import shortuuid

import pandas as pd
from flask import Flask

from app.models import Group, User
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
        list_group = [{
                'key': 'admin',
                'name': 'admin',
                'description': 'admin',
            },
            {
                'key': 'user',
                'name': 'user',
                'description': 'user',
            }
        ]

        list_user = [
            {
            'email': 'cuongadmin@gmail.com',
            'password': '123456789',
            'full_name': 'Nguyễn Ngọc Cương',
            'group_key': 'admin',
            'is_staff': True,
            },{
                'email': 'cuonguser@gmail.com',
                'password': '123456789',
                'full_name': 'Nguyễn Ngọc Cương',
                'group_key': 'user',
            },
            {
                'email': 'locuser@gmail.com',
                'password': '123456789',
                'full_name': 'Tô Thành lộc',
                'group_key': 'user',
            },
            {
                'email': 'locadmin@gmail.com',
                'password': '123456789',
                'full_name': 'Tô Thành lộc',
                'group_key': 'admin',
                'is_staff': True,
            }
        ]

        list_add_group= []
        for item in list_group:
            group = Group(
                id=str(shortuuid.uuid()), **item
            )
            list_add_group.append(group)
        db.session.bulk_save_objects(list_add_group)

        for item in list_user:
            group_key = item.pop('group_key')
            group = Group.query.filter_by(key=group_key).first()
            user = User(id=str(shortuuid.uuid()), **item, group_id=group.id, is_active=True)
            db.session.add(user)
            db.session.flush()

        db.session.commit()

    def delete_group(self):
        User.query.filter().delete()
        Group.query.filter().delete()
        db.session.commit()


if __name__ == '__main__':
    print("=" * 10, f"Starting init Address to the database on the uri: {CONFIG.SQLALCHEMY_DATABASE_URI}", "=" * 10)
    worker = Worker()
    worker.delete_group()
    worker.init_group()
    print("=" * 50, "Add address Success", "=" * 50)
