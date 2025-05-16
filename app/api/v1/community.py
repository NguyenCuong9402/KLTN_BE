import ipaddress
import socket

from flask import Blueprint, request
from sqlalchemy import asc
from sqlalchemy_pagination import paginate

from app.api.helper import send_result, send_error
from app.models import Community
from app.settings import DevConfig
from app.utils import escape_wildcard
from app.validator import CommunitySchema

api = Blueprint('community', __name__)


def is_same_subnet(ip1, ip2, subnet="255.255.255.0"):
    # Chuyển đổi IP thành mạng và kiểm tra xem ip2 có trong mạng của ip1 không
    try:
        network = ipaddress.IPv4Network(f"{ip1}/{subnet}", strict=False)
        return ipaddress.IPv4Address(ip2) in network
    except ValueError:
        return False

def get_local_ip():
    # Lấy địa chỉ IP của server
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # Kết nối đến DNS Google để lấy IP
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

@api.route("", methods=["GET"])
def get_all_community():
    try:
        text_search = request.args.get('text_search', "")

        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        server_ip = get_local_ip()

        query = Community.query.filter()

        if text_search:
            text_search = text_search.strip()
            text_search = text_search.lower()
            text_search = escape_wildcard(text_search)
            text_search = "%{}%".format(text_search)
            query = query.filter(Community.name.ilike(text_search))

        query = query.order_by(asc(Community.created_date))
        paginator = paginate(query, 1, 10)
        communities = CommunitySchema(many=True).dump(paginator.items)
        response_data = dict(
            items=communities,
            total_pages=paginator.pages if paginator.pages > 0 else 1,
            total=paginator.total,
            # current_page=paginator.page,  # Số trang hiện tại
            has_previous=paginator.has_previous,  # Có trang trước không
            has_next=paginator.has_next  # Có trang sau không
        )
        return send_result(data=response_data, message=f"client ip{client_ip} Server: {server_ip}")
    except Exception as ex:
        return send_error(message=f"{DevConfig.SQLALCHEMY_DATABASE_URI}{str(ex)}")


@api.route("/<community_id>", methods=["GET"])
def get_community(community_id):
    item = Community.query.filter(Community.id == community_id).first()
    if item is None:
        return send_error(message="Nhóm không tồn tại, F5 lại web")
    data = CommunitySchema().dump(item)
    return send_result(data=data)
