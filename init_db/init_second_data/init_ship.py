from shortuuid import uuid
from flask import Flask
from app.models import Group, TypeProduct, Region, Shipper, PriceShip
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

    def init_region(self):
        regions = {
            "mien_bac": { "region": [
                "Thành phố Hải Phòng",
                "Tỉnh Bắc Giang",
                "Tỉnh Bắc Kạn",
                "Tỉnh Bắc Ninh",
                "Tỉnh Cao Bằng",
                "Tỉnh Điện Biên",
                "Tỉnh Hà Giang",
                "Tỉnh Hà Nam",
                "Tỉnh Hải Dương",
                "Tỉnh Hòa Bình",
                "Tỉnh Hưng Yên",
                "Tỉnh Lai Châu",
                "Tỉnh Lào Cai",
                "Tỉnh Lạng Sơn",
                "Tỉnh Nam Định",
                "Tỉnh Ninh Bình",
                "Tỉnh Phú Thọ",
                "Tỉnh Quảng Ninh",
                "Tỉnh Sơn La",
                "Tỉnh Thái Bình",
                "Tỉnh Thái Nguyên",
                "Tỉnh Tuyên Quang",
                "Tỉnh Vĩnh Phúc",
                "Tỉnh Yên Bái"
            ],"name":"Miền Bắc"},
            "mien_trung":{"region": [
                "Thành phố Đà Nẵng",
                "Tỉnh Bình Định",
                "Tỉnh Đắk Lắk",
                "Tỉnh Đắk Nông",
                "Tỉnh Gia Lai",
                "Tỉnh Hà Tĩnh",
                "Tỉnh Khánh Hòa",
                "Tỉnh Kon Tum",
                "Tỉnh Nghệ An",
                "Tỉnh Ninh Thuận",
                "Tỉnh Phú Yên",
                "Tỉnh Quảng Bình",
                "Tỉnh Quảng Nam",
                "Tỉnh Quảng Ngãi",
                "Tỉnh Quảng Trị",
                "Tỉnh Thanh Hóa",
                "Tỉnh Thừa Thiên Huế"
            ], "name":"Miền Trung"},
            "mien_nam": {"region":[
                "Thành phố Cần Thơ",
                "Thành phố Hồ Chí Minh",
                "Tỉnh An Giang",
                "Tỉnh Bà Rịa - Vũng Tàu",
                "Tỉnh Bạc Liêu",
                "Tỉnh Bến Tre",
                "Tỉnh Bình Dương",
                "Tỉnh Bình Phước",
                "Tỉnh Bình Thuận",
                "Tỉnh Cà Mau",
                "Tỉnh Đồng Nai",
                "Tỉnh Đồng Tháp",
                "Tỉnh Hậu Giang",
                "Tỉnh Kiên Giang",
                "Tỉnh Lâm Đồng",
                "Tỉnh Long An",
                "Tỉnh Sóc Trăng",
                "Tỉnh Tây Ninh",
                "Tỉnh Tiền Giang",
                "Tỉnh Trà Vinh",
                "Tỉnh Vĩnh Long"
            ],"name": "Miền Nam"},
            "thu_do": {"region": ["Thành phố Hà Nội"],"name":"Thủ đô Hà Nội" },
        }
        list_region= []
        for region_id, value  in regions.items():
            region = Region(
                id=region_id, **value
            )
            list_region.append(region)
        db.session.bulk_save_objects(list_region)
        db.session.commit()

    def delete_region(self):
        Region.query.filter().delete()
        db.session.commit()

    def init_ship(self):
        ships = ["Giao hàng tiết kiệm", "Giao hàng nhanh", "Giao hàng hỏa tốc"]
        list_ships= []
        for index, ship  in enumerate(ships):
            shipper = Shipper(
                id=str(uuid()), name=ship, index=index
            )
            list_ships.append(shipper)
        db.session.bulk_save_objects(list_ships)
        db.session.commit()

    def delete_ship(self):
        Shipper.query.filter().delete()
        db.session.commit()

    def init_ship_price(self):
        # ships = ["Giao hàng tiết kiệm", "Giao hàng nhanh", "Giao hàng hỏa tốc"]
        # regions = ["thu_do", "mien_bac", "mien_trung", "mien_nam"]
        # ships = ["Giao hàng tiết kiệm", "Giao hàng nhanh", "Giao hàng hỏa tốc"]
        # regions = ["thu_do", "mien_bac", "mien_trung", "mien_nam"]
        # ship_region_list = [
        #     {"ship": ship, "region": region, "price": None}
        #     for ship in ships
        #     for region in regions
        # ]
        # print(ship_region_list)

        ship_prices = [{'ship': 'Giao hàng tiết kiệm', 'region': 'thu_do', 'price': 15},
         {'ship': 'Giao hàng tiết kiệm', 'region': 'mien_bac', 'price': 25},
         {'ship': 'Giao hàng tiết kiệm', 'region': 'mien_trung', 'price': 35},
         {'ship': 'Giao hàng tiết kiệm', 'region': 'mien_nam', 'price': 45},
         {'ship': 'Giao hàng nhanh', 'region': 'thu_do', 'price': 20},
         {'ship': 'Giao hàng nhanh', 'region': 'mien_bac', 'price': 30},
         {'ship': 'Giao hàng nhanh', 'region': 'mien_trung', 'price': 40},
         {'ship': 'Giao hàng nhanh', 'region': 'mien_nam', 'price': 50},
         {'ship': 'Giao hàng hỏa tốc', 'region': 'thu_do', 'price': 30},
         {'ship': 'Giao hàng hỏa tốc', 'region': 'mien_bac', 'price': 50},
         {'ship': 'Giao hàng hỏa tốc', 'region': 'mien_trung', 'price': 60},
         {'ship': 'Giao hàng hỏa tốc', 'region': 'mien_nam', 'price': 70}]

        list_ship_prices= []
        for ship_price in ship_prices:
            shipper = Shipper.query.filter_by(name=ship_price.get('ship')).first()
            region = Region.query.filter_by(id=ship_price.get('region')).first()

            price_ship = PriceShip(
                id=str(uuid()), price=ship_price.get('price')*1000,
                region_id=region.id, shipper_id=shipper.id
            )
            list_ship_prices.append(price_ship)
        db.session.bulk_save_objects(list_ship_prices)
        db.session.commit()

    def delete_ship_price(self):
        PriceShip.query.filter().delete()
        db.session.commit()

if __name__ == '__main__':
    print("=" * 10, f"Starting init Price Ship to the database on the uri: {CONFIG.SQLALCHEMY_DATABASE_URI}", "=" * 10)
    worker = Worker()
    worker.delete_region()
    worker.delete_ship()
    worker.delete_ship_price()
    worker.init_region()
    worker.init_ship()
    worker.init_ship_price()
    print("=" * 50, "Add address Success", "=" * 50)
