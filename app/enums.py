from app.settings import DevConfig
from datetime import time
MONGO_COLLECTION_STATISTIC_ATTENDANCE_USER = "attendance_statistics"
TIME_FORMAT_LOG = "[%Y-%b-%d %H:%M]"

ADMIN_EMAIL = DevConfig.ADMIN_EMAIL

ALLOWED_EXTENSIONS_IMG = ['.jpeg', '.jpg', '.png']

TYPE_REACTION = {
    'ARTICLE': 'article',
    'COMMENT': 'comment',
}

ADMIN_KEY_GROUP = ['admin']
USER_KEY_GROUP = "user"
KEY_GROUP_NOT_STAFF = ['admin', 'user']

STATUS_ORDER = {
    'PENDING': 'pending',
    'DELIVERING': 'delivering',
    'RESOLVED': 'resolved',
}

NOTIFY_TYPE = {
    "ARTICLE": 'article',
    "COMMENT": 'comment',
    "REACTION": 'reaction',
    "ORDERS": 'orders',
    "DELIVERING_ORDERS": 'delivering_orders',

}

CONTENT_TYPE = {
    "ARTICLE": 'article',
    "COMMENT": 'comment',
    "REACTION": 'reaction',
    "ORDERS": 'orders',
}

ATTENDANCE_STATUS = {
    'PRESENT': 'present',   # Đầy đủ
    'MISSING': 'missing',   # Thiếu
    'ABSENT': 'absent',       # Nghỉ
    'ACCEPT_ABSENT': 'accept_absent'  # Nghỉ chấp nhận được (Thứ 7, Chủ nhật)
}

ATTENDANCE = {
    'CHECK_IN': time(8, 0),  # 8:00 AM
    'CHECK_OUT': time(17, 30)
}

WORK_UNIT_TYPE = {
    "HALF": "half", # Đi làm muộn, về sớm
    "FULL": "full"  # đi làm đúng giờ
}

# processing, resolved

REPORT_ORDER_TYPE = {
    'PROCESSING': 'processing',
    'RESOLVED': 'resolved'
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

TYPE_ACTION_SEND_MAIL = {
    'REGISTER': 'register',
    'OPEN_ACCOUNT': 'open_account',
    'UPDATE_ACCOUNT': 'update_account',
    'CHANGE_PASS': 'change_pass',
    'FORGET_PASS': 'forget_pass',
    'NEW_PASSWORD': 'new_password',
}

TYPE_FILE_LINK = {
    'USER': 'user',
    'PRODUCT': 'product',
    'ORDER_REPORT': 'order_report',
}


MAIL_VERITY_CODE = 'verity_register'
GROUP_ADMIN_KEY = 'admin'
GROUP_USER_KEY = 'user'
GROUP_KEY_PARAM = {
    "is_supper_admin": "/admin/dashboard",
    "is_staff": "/timekeeping",
    "user": "/",
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
        "Tỉnh Hoà Bình",
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

# Prompt cố định
PROMPT_AI = """
Bạn là AI chuyên phân tích yêu cầu mua sắm thời trang từ người dùng tại Việt Nam.

**Nhiệm vụ của bạn** là phân tích một đoạn văn tiếng Việt để trích xuất các thông tin sau:
1. **Giá tối thiểu**: Giá người dùng mong muốn tìm sản phẩm, nếu có. Nếu không có giá tối thiểu, trả về null.
2. **Giá tối đa**: Giá cao nhất mà người dùng sẵn sàng chi trả, nếu có. Nếu không có giá tối đa, trả về null.
3. **Loại sản phẩm**: Danh sách các loại sản phẩm mà người dùng yêu cầu tìm kiếm, lấy từ danh sách sau: [#LIST_SAN_PHAM]. Bạn chỉ được chọn các sản phẩm có trong danh sách này.

**Cách phân tích**:
1. **Thời tiết và mùa** tại Việt Nam có sự phân hóa rõ rệt giữa các vùng miền và mùa trong năm:
   - **Mùa hè** (tháng 4 đến tháng 8) thường rất nóng, đặc biệt là các khu vực miền Nam và miền Trung. 
   - **Mùa thu** (tháng 9 đến tháng 11) thời tiết mát mẻ, đôi khi có mưa, nhưng vẫn không quá lạnh.
   - **Mùa đông** (tháng 12 đến tháng 2) ở miền Bắc và miền Trung khá lạnh, cần áo khoác hoặc sản phẩm giữ ấm.
   - **Mùa xuân** (tháng 3) cũng có thời tiết mát mẻ, không quá lạnh.

2. **Nếu không có thông tin rõ ràng về mùa**, bạn cần phải suy luận từ các yếu tố khác trong đoạn văn:
   - **Từ khóa chỉ mùa hoặc thời tiết**: Nếu không có từ khóa trực tiếp như "mùa hè", "mùa đông", "lạnh", "nóng", bạn cần xem xét các từ mô tả cảm giác hoặc hành vi của người mua sắm. 
   Ví dụ: "mặc vào mùa thu", "mặc cho thời tiết ấm", "cần áo mát", "nên mặc áo giữ ấm", "áo cho thời tiết mưa".
   - **Các từ khóa cảm giác**: Tìm kiếm các từ mô tả cảm giác về nhiệt độ, ví dụ: "ấm", "mát mẻ", "lạnh", "nóng".
    Những từ này sẽ giúp xác định mùa.
   - **Các từ mô tả tính chất thời tiết**: "Mưa", "gió", "khô ráo", "nắng", "lạnh", "ẩm ướt" có thể giúp suy luận mùa hoặc thời điểm trong năm.

3. **Giá**: Nếu trong đoạn văn có đề cập đến giá hoặc khoảng giá (ví dụ: "khoảng 300 nghìn đến 1 triệu VNĐ"), bạn cần xác định và trả về giá tối thiểu và tối đa.
   - Nếu chỉ có một giá duy nhất, hãy xác định là giá tối đa hoặc tối thiểu tùy thuộc vào cách người dùng diễn đạt.
   - Nếu không có giá cụ thể, trả về `null` cho cả hai trường giá.

**Lưu ý**:
- Chỉ trả về JSON, không thêm giải thích.
- Các loại sản phẩm phải nằm trong danh sách cho trước, và danh sách không bao gồm các sản phẩm ngoài danh sách này.

**Ví dụ yêu cầu**:
- "Tôi muốn tìm áo mùa hè khoảng 300 nghìn đến 1 triệu VNĐ."
**Kết quả mong muốn**:

Với yêu cầu: "Tôi muốn tìm áo mùa hè khoảng 300 nghìn đến 1 triệu VNĐ."
   Kết quả:
   ```json
   {
     "min_price": 300000,
     "max_price": 1000000,
     "type": ["Áo sơ mi", "Áo phông"]
   }
"""

PROMPT_AI_ABOUT_US = """
    Bạn là một nhà thơ AI chuyên sáng tác thơ quảng bá.

Hãy sáng tác một bài thơ lục bát, theo luật thơ lục bát truyền thống Việt Nam, để giới thiệu một shop thời trang nam chuyên bán quần áo và phụ kiện.

Thông tin cần đưa vào bài thơ:

Tên cửa hàng: C&N
Nhân viên hỗ trợ cực kì nồng nhiệt, và shop rất hân hoan được phục vụ
Giờ làm việc: 8:00 - 20:00
Hệ thống cửa hàng:
116 Bùi Xương Trạch, Thanh Xuân, Hà Nội
286 Nguyễn Xiển, Thanh Xuân, Hà Nội
Số 5 Giáp Bát, Hoàng Mai, Hà Nội

Yêu cầu:

Thơ mang phong cách vui vẻ, thân thiện, gần gũi, giản dị của
Giúp người đọc cảm thấy thiện cảm và muốn ghé thăm cửa hàng
Kết bài có thể gợi ý liên hệ hoặc ghé shop
    """

