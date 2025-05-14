from flask import Blueprint, request
from sqlalchemy import asc, desc

from sqlalchemy_pagination import paginate

from app.api.helper import send_result, send_error
from app.enums import KEY_GROUP_NOT_STAFF
from app.gateway import authorization_require
from app.models import Group
from app.utils import escape_wildcard
from app.validator import GroupSchema

api = Blueprint('group', __name__)

@api.route("/<group_id>", methods=["GET"])
@authorization_require()
def get_item(group_id):
    try:
        item = Group.query.filter(Group.id == group_id).first()
        if item is None:
            return send_error(message="Chức vụ không tồn tại")
        data = GroupSchema(many=False).dump(item)
        return send_result(data=data)
    except Exception as ex:
        return send_error(message=str(ex))

@api.route("", methods=["GET"])
@authorization_require()
def get_items():
    try:

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        order_by = request.args.get('order_by', 'name')
        sort = request.args.get('sort', 'desc')
        text_search = request.args.get('text_search', None)

        query = Group.query.filter(Group.key.notin_(KEY_GROUP_NOT_STAFF))

        if text_search:
            text_search = text_search.strip()
            text_search = text_search.lower()
            text_search = escape_wildcard(text_search)
            text_search = "%{}%".format(text_search)
            query = query.filter(Group.name.ilike(text_search))

        column_sorted = getattr(Group, order_by)

        query = query.order_by(desc(column_sorted)) if sort == "desc" else query.order_by(asc(column_sorted))

        paginator = paginate(query, page, page_size)

        groups = GroupSchema(many=True).dump(paginator.items)

        response_data = dict(
            items=groups,
            total_pages=paginator.pages if paginator.pages > 0 else 1,
            total=paginator.total,
            # current_page=paginator.page,  # Số trang hiện tại
            has_previous=paginator.has_previous,  # Có trang trước không
            has_next=paginator.has_next  # Có trang sau không
        )
        return send_result(data=response_data)
    except Exception as ex:
        return send_error(message=str(ex))
