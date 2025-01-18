import json
import os
from shortuuid import uuid
import pandas as pd
from flask import Flask

from app.models import Address
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

    def init_address(self):
        file_name = "TinhHuyenXa2021.xlsx"
        # import permission
        df = pd.read_excel(file_name, sheet_name='Sheet1')
        list_add_address = []
        for index, row in df.iterrows():
            if pd.isna(row['province']) or pd.isna(row['district']) or pd.isna(row['ward']):
                continue
            address = Address.query.filter(Address.province == row['province'], Address.district == row['district'],
                                           Address.ward == row['ward'] ).first()
            if address is None:
                address = Address(
                    id=str(uuid()),
                    province=row['province'],
                    district=row['district'],
                    ward=row['ward']
                )
                list_add_address.append(address)
        db.session.bulk_save_objects(list_add_address)
        db.session.commit()

    def delete_address(self):
        Address.query.filter().delete()
        db.session.commit()



if __name__ == '__main__':
    print("=" * 10, f"Starting init Address to the database on the uri: {CONFIG.SQLALCHEMY_DATABASE_URI}", "=" * 10)
    worker = Worker()
    worker.delete_address()
    worker.init_address()
    print("=" * 50, "Add address Success", "=" * 50)