import json
import os
import random

from alembic.util import status
from shortuuid import uuid
import pandas as pd
from flask import Flask
from datetime import datetime, date, timedelta, time
from dateutil.relativedelta import relativedelta
from sqlalchemy import func

from app.api.helper import send_result
from app.enums import regions, STATUS_ORDER
from app.models import Group, Community, Attendance, User, Orders, Shipper, PriceShip, Product, OrderItems
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

    def get_timestamp_x_months_ago(self, i):
        target_date = datetime.now() - relativedelta(months=i)
        target_date = target_date.replace(day=15, hour=0, minute=0, second=0, microsecond=0)
        return int(target_date.timestamp())


    def init_orders(self):

        try:
            users = User.query.filter(User.group.has(is_staff=False, is_super_admin=False)).limit(100).all()
            ship_ids = [ship.id for ship in Shipper.query.all()]

            all_prices = {(p.region_id, p.shipper_id): p.price for p in PriceShip.query.all()}

            for user in users:
                all_products = Product.query.order_by(func.random()).limit(3).all()

                for i in range(20):
                    time_stamp = self.get_timestamp_x_months_ago(i)
                    ship_id = random.choice(ship_ids)

                    region_id = next((key for key, value in regions.items() if user.address.get('province') in value),
                                     '')
                    price_ship = all_prices.get((region_id, ship_id), 0)

                    order = Orders(
                        id=str(uuid()), user_id=user.id, full_name=user.full_name, phone_number=user.phone,
                        address_id=user.address_id, created_date=time_stamp, modified_date=time_stamp,
                        ship_id=ship_id, price_ship=price_ship, status=STATUS_ORDER.get('RESOLVED')
                    )
                    db.session.add(order)
                    db.session.flush()  # Để có `order.id` cho OrderItems

                    total_price = price_ship
                    for product in all_products:
                        order_item = OrderItems(
                            id=str(uuid()), order_id=order.id, product_id=product.id,
                            size_id=product.sizes[0].id, color_id=product.colors[0].id,
                            count=product.detail.get('price', 1)  # Default tránh lỗi None
                        )
                        db.session.add(order_item)
                        total_price += product.detail.get('price', 1)

                    order.count = total_price
                    db.session.flush()

            db.session.commit()

        except Exception as ex:
            print("Lỗi:", str(ex))

    def delete_orders(self):
        Orders.query.filter().delete()
        db.session.commit()


if __name__ == '__main__':
    print("=" * 10, f"Starting init attendance to the database on the uri: {CONFIG.SQLALCHEMY_DATABASE_URI}", "=" * 10)
    worker = Worker()
    worker.delete_orders()
    worker.init_orders()
    print("=" * 50, "Add address Success", "=" * 50)
