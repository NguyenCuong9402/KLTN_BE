import json
import os
from shortuuid import uuid
import pandas as pd
from flask import Flask

from app.models import Role, Permission, RolePermission, Group, GroupRole
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

    def init_role_permisson(self):
        file_name = "role_permisson.xlsx"
        # import permission
        df = pd.read_excel(file_name)
        df[['KEY', 'ROLE', 'GROUP_KEY']] = df[['KEY', 'ROLE', 'GROUP_KEY']].ffill()
        dict_data = {}
        for index, row in df.iterrows():
            if dict_data.get(row['KEY'], None) is None:
                dict_data[row['KEY']] = {
                    'name': row['ROLE'],
                    'group_key': row['GROUP_KEY'],
                    'permission': []
                }
            dict_data[row['KEY']]['permission'].append(row['PERMISSION'])

        for key, value in dict_data.items():
            role = Role(id=str(uuid()), key=key, name=value.get('name'))
            db.session.add(role)
            db.session.flush()
            if value.get('group_key') == 'all':
                list_group = ['user', 'admin', 'manager', 'employee']
            else:
                list_group = [g.strip() for g in value.get('group_key', '').split(',') if g.strip()]
            for group_key in list_group:
                group = Group.query.filter_by(key=group_key).first()
                if group:
                    group_role = GroupRole(id=str(uuid()), role_id=role.id, group_id=group.id)
                    db.session.add(group_role)
                    db.session.flush()
            list_role_per = []
            for resource in value['permission']:
                permission = Permission(id=str(uuid()), resource=resource)
                db.session.add(permission)
                db.session.flush()
                role_per = RolePermission(id=str(uuid()), role_id=role.id, permission_id=permission.id)
                list_role_per.append(role_per)

            db.session.bulk_save_objects(list_role_per)
            db.session.flush()

        db.session.commit()

    def delete_role_permission(self):
        Role.query.filter().delete()
        Permission.query.filter().delete()

        db.session.commit()


if __name__ == '__main__':
    print("=" * 10, f"Starting init init_role_permisson to the database on the uri: {CONFIG.SQLALCHEMY_DATABASE_URI}", "=" * 10)
    worker = Worker()
    worker.delete_role_permission()
    worker.init_role_permisson()
    print("=" * 50, "Add init_role_permisson Success", "=" * 50)