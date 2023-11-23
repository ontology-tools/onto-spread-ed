import datetime

from flask import jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy

from ...guards.admin import verify_admin

from ...database.Release import Release


bp = Blueprint("api_release", __name__, url_prefix="/api/release")

@bp.route("start", methods=("POST",))
@verify_admin
def release_start(db: SQLAlchemy):
    release = Release(state="starting", start=datetime.datetime.now(), step=0, current_info={})
    db.session.add(release)
    db.session.commit()

    return jsonify(release.as_dict())
