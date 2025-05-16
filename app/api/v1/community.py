import ipaddress
import requests
from flask import Blueprint, request
from sqlalchemy import asc
from sqlalchemy_pagination import paginate

from app.api.helper import send_result, send_error
from app.models import Community
from app.settings import DevConfig
from app.utils import escape_wildcard
from app.validator import CommunitySchema
def get_public_ipv6():
    try:
        response = requests.get("https://api64.ipify.org", timeout=3)
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print("Lỗi khi lấy IPv6:", e)
    return None
api = Blueprint('community', __name__)


def is_same_ipv6_subnet(ip1, ip2, prefix_length=64):
    try:
        network = ipaddress.IPv6Network(f"{ip1}/{prefix_length}", strict=False)
        ip2_addr = ipaddress.IPv6Address(ip2)
        return ip2_addr in network
    except ValueError:
        return False


@api.route("", methods=["GET"])
def get_all_community():
    try:
        text_search = request.args.get('text_search', "")

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
        return send_result(data=response_data, message="Oke")
    except Exception as ex:
        return send_error(message=f"{DevConfig.SQLALCHEMY_DATABASE_URI}{str(ex)}")


@api.route("/<community_id>", methods=["GET"])
def get_community(community_id):
    item = Community.query.filter(Community.id == community_id).first()
    if item is None:
        return send_error(message="Nhóm không tồn tại, F5 lại web")
    data = CommunitySchema().dump(item)
    return send_result(data=data)

@api.route("/test", methods=["GET"])
def get_community_test():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

    server_ip = get_public_ipv6()
    check = is_same_ipv6_subnet(server_ip, client_ip)

    data = {
        'client_ip': client_ip,
        'server_ip': server_ip,
        'check': check,
    }
    return send_result(data=data, message="Done")