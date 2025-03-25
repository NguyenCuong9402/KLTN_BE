import json

from shortuuid import uuid
from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy import desc, asc
from sqlalchemy_pagination import paginate

from app.enums import LAYER_COMMENT
from app.extensions import logger, db
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request_optional
from app.api.helper import send_result, send_error, get_user_id_request
from app.models import User, Article, Comment
from app.utils import trim_dict
from app.validator import  CommentValidation, CommentParamsValidation, CommentSchema

api = Blueprint('comment', __name__)


@api.route('', methods=['POST'])
@jwt_required
def create_comment():
    try:
        user_id = get_jwt_identity()
        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = CommentValidation()
        is_not_validate = validator_input.validate(json_body)

        article_id = json_body.get('article_id', None)
        ancestry_id = json_body.get('ancestry_id', None)

        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')

        if Article.query.filter_by(id=article_id).first() is None:
            return send_error(message="Bài viết không tồn tại")
        if ancestry_id:
            if Comment.query.filter_by(id=ancestry_id, article_id=article_id).first() is None :
                return send_error(message="Comment được trả lời không tồn tại.")
        mention_usernames = json_body.pop('mention_usernames', [])
        comment = Comment(id=str(uuid()), user_id=user_id, **json_body)
        db.session.add(comment)
        db.session.flush()
        db.session.commit()
        data = CommentSchema(context={"user_id": user_id}).dump(comment)

        return send_result(data=data, message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


@api.route("/<comment_id>", methods=["DELETE"])
@jwt_required
def remove_comment(comment_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.filter(User.id == user_id).first()
        if user is None:
            return send_error(message='User not found', code=404)
        comment = Comment.query.filter(Comment.id == comment_id, user.id == user.id)
        if comment.first() is None:
            return send_error(message='Comment not found', code=404)
        comment.delete()
        db.session.flush()
        db.session.commit()
        return send_result(message="Xóa bình luận thành công")
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))


@api.route('/<comment_id>/children', methods=['GET'])
def get_comment(comment_id):
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = CommentParamsValidation().load(params) if params else dict()
        except ValidationError as err:
            logger.error(json.dumps({
                "message": err.messages,
                "data": err.valid_data
            }))
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)
        page = params.get('page', 1)
        page_size = params.get('page_size', 10)
        order_by = params.get('order_by', 'created_date')
        sort = params.get('sort', 'desc')

        query = Comment.query.filter(Comment.ancestry_id == comment_id)
        user_id = get_user_id_request()


        query = query.order_by(desc(Comment.created_date)) if sort == "desc" else query.order_by(asc(Comment.created_date))


        paginator = paginate(query, page, page_size)
        comments = CommentSchema(many=True, context={"user_id": user_id, "order_by": order_by,
                                                     "sort": sort, "depth": LAYER_COMMENT}).dump(paginator.items)



        response_data = dict(
            items=comments,
            total_pages=paginator.pages if paginator.pages > 0 else 1,
            total=paginator.total,
            has_previous=paginator.has_previous,  # Có trang trước không
            has_next=paginator.has_next,  # Có trang sau không
            remaining_count = max(paginator.total - page_size * page, 0)
        )


        return send_result(data= response_data,  message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)

@api.route('/<comment_id>', methods=['GET'])
def get_comment_detail(comment_id):
    try:

        query = Comment.query.filter(Comment.id == comment_id).first()
        if not query:
            return send_error(message="Comment không tồn tại", code=404)
        user_id = get_user_id_request()
        comment = CommentSchema(
            context={"user_id": user_id},
            only=("id", "body", "created_date", "ancestry_id", "user", "article", "has_reacted", "reaction_count",
                  "reply_count")
        ).dump(query)

        return send_result(data=comment,  message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


