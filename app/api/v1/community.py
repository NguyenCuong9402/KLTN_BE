import socket
from ipaddress import ip_address, IPv4Address, IPv4Network

from flask import Blueprint, request
from sqlalchemy import asc
from sqlalchemy_pagination import paginate

from app.api.helper import send_result, send_error
from app.models import Community
from app.settings import DevConfig
from app.utils import escape_wildcard
from app.validator import CommunitySchema

api = Blueprint('community', __name__)

def get_client_ipv4(request):
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    try:
        ip_obj = ip_address(ip)
        if isinstance(ip_obj, IPv4Address):
            return str(ip_obj)
    except:
        return None

def same_subnet(ip1, ip2, mask="255.255.255.0"):
    net1 = IPv4Network(f"{ip1}/{mask}", strict=False)
    return ip2 in net1

def get_server_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return "127.0.0.1"
    finally:
        s.close()


@api.route("", methods=["GET"])
def get_all_community():
    try:
        text_search = request.args.get('text_search', "")

        client_ip = get_client_ipv4(request)
        server_ip = get_server_ip()

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
        return send_result(data=response_data, message=f"Client: {client_ip} "
                                                       f"Server: {server_ip}")
    except Exception as ex:
        return send_error(message=f"{DevConfig.SQLALCHEMY_DATABASE_URI}{str(ex)}")


@api.route("/<community_id>", methods=["GET"])
def get_community(community_id):
    item = Community.query.filter(Community.id == community_id).first()
    if item is None:
        return send_error(message="Nhóm không tồn tại, F5 lại web")
    data = CommunitySchema().dump(item)
    return send_result(data=data)
