from app.settings import DevConfig
from datetime import datetime, date, time

TIME_FORMAT_LOG = "[%Y-%b-%d %H:%M]"

ADMIN_EMAIL = DevConfig.ADMIN_EMAIL

ALLOWED_EXTENSIONS_IMG = ['.jpeg', '.jpg', '.png']

TYPE_REACTION = {
    'ARTICLE': 'article',
    'COMMENT': 'comment',
}

ADMIN_KEY_GROUP = ['admin']

KEY_GROUP_NOT_STAFF = ['admin', 'user']

STATUS_ORDER = {
    'PENDING': 'pending',
    'DELIVERING': 'delivering',
    'RESOLVED': 'resolved',
}

ATTENDANCE_STATUS = {
    'PRESENT': 'present',   # Đầy đủ
    'MISSING': 'missing',   # Thiếu
    'ABSENT': 'absent',       # Nghỉ
    'ACCEPT_ABSENT': 'accept_absent'  # Nghỉ chấp nhận được (Thứ 7, Chủ nhật)
}

ATTENDANCE = {
    'CHECK_IN': time(8, 0),  # 8:00 AM
    'LATE_CHECK_IN': time(13, 30),  # 1:30 PM
    'CHECK_OUT': time(17, 30)
}

WORK_UNIT_TYPE = {
    "HALF": "half",
    "FULL": "full"
}

TYPE_PAYMENT_ONLINE = {
    'MOMO': 'momo',
    'ZALO': 'zalo',
}

TYPE_PAYMENT = {
    'MOMO': 'momo',
    'ZALO': 'zalo',
    'COD' : 'cod'
}

LAYER_COMMENT = 2

TYPE_FILE_LINK = {
    'USER': 'user',
    'PRODUCT': 'product',
    'ORDER_REPORT': 'order_report',
}

TOKEN_BOT_TELE = "7727055654:AAFJnBNiMv58Vy46mjxXFVyaW-geF3nFZ18"

MAIL_VERITY_CODE = 'verity_register'
GROUP_ADMIN_KEY = 'admin'
GROUP_USER_KEY = 'user'
GROUP_KEY_PARAM = {
    "user": "/",
    "admin":"/admin/dashboard"
}

MOMO_CONFIG = {
    "momo_api_create_payment": "https://test-payment.momo.vn/v2/gateway/api/create",
    "momo_api_check_payment": "https://test-payment.momo.vn/v2/gateway/api/query",
    "redirectUrl": "about:blank",
    "accessKey": "F8BBA842ECF85",
    "secretKey": "K951B6PE1waDMi640xX08PD3vg6EkVlz",
    "partnerCode": "MOMO",
    "partnerName" : "MoMo Payment",
    "requestType": "payWithMethod",
    "extraData": "",
    "autoCapture": True,
    "lang": "vi",
    "storeId": "Test Store",
    "orderGroupId": "",
    "status_success": 0
}

ZALO_CONFIG = {
    "key1": "PcY4iZIKFCIdgZvA6ueMcMHHUbRLYjPL",
    "key2": "kLtgPl8HHhfvMuDHPwKfgfsY4Ydm9eIz",
    "app_id":2553,
    "app_user": "user123",
    "bank_code": "zalopayapp",
    "zalo_api_create_payment": "https://sb-openapi.zalopay.vn/v2/create",
    "zalo_api_check_payment": "https://sb-openapi.zalopay.vn/v2/query",
    "status_success": 1
}

DURATION_SESSION_MINUTES = 100

regions = {
    "mien_bac": [
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
    ],
    "mien_trung": [
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
    ],
    "mien_nam": [
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
    ],
    "thu_do": ["Thành phố Hà Nội"],
}

