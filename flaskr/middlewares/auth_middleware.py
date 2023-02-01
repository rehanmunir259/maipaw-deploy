from functools import wraps
import jwt
from flask import request, abort
from flask import current_app
from ..db import get_db
from ..models.objectid import PydanticObjectId

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        if not token:
            return {
                "message": "Authentication Token is missing!",
                "data": None,
                "error": "Unauthorized"
            }, 401
        try:
            data=jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
#             get role and compare to data
            db = get_db()
            roles_collection = db.roles
            admin_role = roles_collection.find_one({'name':'admin'})
            users = db.users
            print(data)
            current_user = users.find_one({'_id': PydanticObjectId(data["id"]), 'role': PydanticObjectId(data['role_id'])})
            if current_user is None:
                return {
                "message": "Invalid Authentication token!",
                "data": None,
                "error": "Unauthorized"
            }, 401
#             if not current_user["active"]:
#                 abort(403)
        except Exception as e:
            return {
                "message": "Something went wrong",
                "data": None,
                "error": str(e)
            }, 500

        return f()
#         return f(current_user, *args, **kwargs)

    return decorated