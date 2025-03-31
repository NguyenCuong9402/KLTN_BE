from shortuuid import uuid
from flask import Blueprint, request
from app.enums import TYPE_REACTION
from app.extensions import db
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.api.helper import send_result, send_error
from app.models import Reaction, Article, Comment
from app.signal import handle_reaction_notification
from app.utils import trim_dict, get_timestamp_now
from app.validator import  ReactionValidation

api = Blueprint('reaction', __name__)


@api.route('', methods=['POST'])
@jwt_required
def toggle_reaction():
    try:
        user_id = get_jwt_identity()
        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = ReactionValidation()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')

        category = json_body['category']
        reactable_id = json_body['reactable_id']

        if category == TYPE_REACTION.get('ARTICLE'):
            check_exist = Article.query.filter_by(id=reactable_id).first()
        else:
            check_exist = Comment.query.filter_by(id=reactable_id).first()

        if check_exist is None:
            return send_error(message=f'{category} đã bị xóa')

        reaction = Reaction.query.filter_by(
            reactable_id=reactable_id,
            user_id=user_id,
            category=category
        ).first()

        handle_notify = False

        if reaction:
            reaction.vote = not reaction.vote
            reaction.modified_date = get_timestamp_now()
        else:
            reaction = Reaction(id=str(uuid()), user_id=user_id,**json_body)
            db.session.add(reaction)

            handle_notify = True

        db.session.flush()
        db.session.commit()

        if handle_notify:
            try:
                handle_reaction_notification(reaction)
            except:
                pass

        return send_result(message='Thành công', data= reaction.vote)

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)