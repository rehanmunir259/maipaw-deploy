import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db
from flask_mail import Mail, Message
from flask import current_app, g, jsonify, make_response
from ..models.model import User, Role
from random import randrange
import random
import math
import jwt
from datetime import datetime, timedelta
from ..models.objectid import PydanticObjectId
from ..middlewares.auth_middleware import token_required
from bson.json_util import dumps, loads


bp = Blueprint('auth', __name__, url_prefix='/auth')

EMAIL_ALREADY_REGISTERED = 'Email already registered'
USER_REGISTERED_MESSAGE = 'User registered successfully'
ADMIN_REGISTERED_MESSAGE = 'Admin registered successfully'
SUCCESS_STATUS = 'Successful'
FAIL_STATUS = 'Failed'
INCORRECT_PASSWORD = 'Incorrect password'
EMAIL_NOT_FOUND = 'Email not found'
EMAIL_REQUIRED = 'Email is required'
EMAIL_SENT = 'Email sent successfully'
USER = 'user'
ADMIN = 'admin'
EMPTY_CODE = ''
FALSE = False
ACCESS_BLCOKED_BY_ADMIN = 'Access blocked by admin'
USER_ALREADY_BLOCKED = 'User is already blocked'
USER_ALREADY_UNBLOCKED = 'User is not blocked'
TRUE = True
USER_BLOCKED_SUCCESSFULLY = 'User blocked successfully'
USER_UNBLOCKED_SUCCESSFULLY = 'User unblocked successfully'



@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
        if error is None:
            try:
                users = db.users
                check = users.find_one({"email":email})
                roles_collection = db.roles
                role = roles_collection.find_one({'name': USER})

                if(check):
                    response = make_response(
                                    jsonify(
                                        {
                                            "status": str(FAIL_STATUS),
                                            "message": str(EMAIL_ALREADY_REGISTERED)
                                        }
                                    ),
                                    406,
                                )
                else:
                    code = generateCode()
                    hash = generate_password_hash(code)
                    user = User(email=email, code=hash, role=role['_id'], is_blocked=FALSE)
                    new_user = users.insert_one(user.to_bson())
                    print(code, email)
                    sendEmail(code=code, email=email)

                    response = make_response(
                                     jsonify(
                                          {
                                            "status": str(SUCCESS_STATUS),
                                            "message": str(USER_REGISTERED_MESSAGE)
                                          }
                                     ),
                                     201,
                                     )

            except Exception as e:
                error = f"User {email} is already registered."

        flash(error)

    response.headers["Content-Type"] = "application/json"
    return response


@bp.route('/generate_code_and_email', methods=('GET', 'POST'))
def generate_code_and_email():
    if request.method == 'POST':
        email = request.form.get('email')
        db = get_db()
        error = None

        if not email:
            error = EMAIL_REQUIRED
        if error is None:
            try:
                users = db.users
                check = users.find_one({"email":email})

                if not check:
                    response = make_response(
                                    jsonify(
                                        {
                                            "status": str(FAIL_STATUS),
                                            "message": str(EMAIL_NOT_FOUND)
                                        }
                                    ),
                                    406,
                                )
                elif check['is_blocked']:
                    response = make_response(
                                        jsonify(
                                                {
                                                    'status': FAIL_STATUS,
                                                    'message': ACCESS_BLCOKED_BY_ADMIN
                                                }
                                            ),
                                            400
                                        )
                else:
                    code = generateCode()
                    hash = generate_password_hash(code)
                    sendEmail(email=email, code=code)
                    users.find_one_and_update({
                                                  "email" : email
                                                },{
                                                  '$set': {
                                                    'code' : hash
                                                  },
                                                })
                    response = make_response(
                                     jsonify(
                                          {
                                            "status": str(SUCCESS_STATUS),
                                            "message": str(EMAIL_SENT)
                                          }
                                     ),
                                     201,
                                     )

            except Exception as e:
                response = make_response(e)
        else:
            response = make_response(
                             jsonify(
                                      {
                                        "status": str(FAIL_STATUS),
                                         "message": error
                                      }
                                     ),
                             400,
                             )
        flash(error)

    response.headers["Content-Type"] = "application/json"
    return response



@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        error = None
        db = get_db()
        users = db.users
        user = users.find_one({"email":email})

        if user is None:
            error = EMAIL_NOT_FOUND
            response = make_response(
                              jsonify(
                                         {
                                             "status": str(FAIL_STATUS),
                                             "message": str(EMAIL_NOT_FOUND)
                                         }
                                         ),
                                         404,
                              )
        elif not check_password_hash(user['code'], password):
            error = INCORRECT_PASSWORD
            response = make_response(
                              jsonify(
                                         {
                                             "status": str(FAIL_STATUS),
                                             "message": str(INCORRECT_PASSWORD)
                                         }
                                         ),
                                         401,
                              )

        if error is None:
            token = ''
            roles_collection = db.roles
            admin_role = roles_collection.find_one({'name':'admin'})
            user = User(**user).to_json()
            response_obj = {}
            if( PydanticObjectId(admin_role['_id']) == PydanticObjectId(user['role'])):
                token = jwt.encode({
                            'role_id': user['role'],
                            'id': user['_id'],
                            'exp' : datetime.utcnow() + timedelta(minutes = 1440)
                        }, current_app.config['SECRET_KEY'])
                response_obj['token'] = token

            users.update_one({
              '_id': PydanticObjectId(user['_id'])
            },{
              '$set': {
                'code': ''
              }
            }, upsert=False)

            session.clear()
            response_obj['status'] = str(SUCCESS_STATUS)
            response = make_response(
                              jsonify(
                                        response_obj
                                        ),
                                        201,
                              )
#             session['user_id'] = user['id']
            return response

        flash(error)

    return response



@bp.route('/getAllEmails', methods=('GET', 'POST'))
@token_required
def getAllEmails():
    db = get_db()
    users_collection = db.users
    users = users_collection.find({},{'email':1})
    users = [User(**doc).to_json() for doc in users]
    response = make_response(
                        jsonify(
                            {
                               "status": str(SUCCESS_STATUS),
                                "users": users
                            }
                            ),
                            200,
                        )
    response.headers["Content-Type"] = "application/json"
    return response


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()



@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))



def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view



def generateCode():
    digits = [i for i in range(0, 10)]
    random_str = ""
    for i in range(6):
        index = math.floor(random.random() * 10)
        random_str += str(digits[index])
    return random_str


def sendEmail(email, code):
    try:
        mail = Mail(current_app)
        msg = Message('Hello from the other side!', sender = 'mockemails135@gmail.com', recipients = [email])
        msg.body = f"Your password for signing in is {code}"
        mail.send(msg)
    except Exception as e:
        flash(e)




@bp.route('/register_admin', methods=('GET', 'POST'))
@token_required
def register_admin():
    if request.method == 'POST':
        response = make_response()
        email = request.form['email']
        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
        if error is None:
            try:
                users = db.users
                check = users.find_one({"email":email})

                if(check):
                    response = make_response(
                                    jsonify(
                                        {
                                            "status": str(FAIL_STATUS),
                                            "message": str(EMAIL_ALREADY_REGISTERED)
                                        }
                                    ),
                                    406,
                                )
                else:
                    roles_collection = db.roles
                    role = roles_collection.find_one({'name': ADMIN})
                    print(role)
                    print(role['_id'])
                    user = User(email=email, code=EMPTY_CODE, role=role['_id'], is_blocked=FALSE)
                    print(user)
                    new_user = users.insert_one(user.to_bson())
                    print(new_user)
                    response = make_response(
                                     jsonify(
                                          {
                                            "status": str(SUCCESS_STATUS),
                                            "message": str(ADMIN_REGISTERED_MESSAGE)
                                          }
                                     ),
                                     201,
                                     )

            except Exception as e:
                error = f"User {email} is already registered."
                response = make_response(
                                      jsonify(
                                             {
                                              "status": str(FAIL_STATUS),
                                              "error": str(e)
                                              }
                                              ),
                                         500,
                                     )
        flash(error)

    response.headers["Content-Type"] = "application/json"
    return response



@bp.route('/block', methods=('GET', 'PATCH'))
@token_required
def block():
    if request.method == 'PATCH':
        email = request.form.get('email')
        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
        if error is None:
            try:
                users = db.users
                user = users.find_one({"email":email})

                if user is None:
                    error = EMAIL_NOT_FOUND
                    response = make_response(
                                     jsonify(
                                            {
                                              "status": str(FAIL_STATUS),
                                              "message": str(EMAIL_NOT_FOUND)
                                            }
                                            ),
                                            404,
                                     )


                else:
                    if(user['is_blocked']):
                        response = make_response(
                                              jsonify(
                                                   {
                                                        'status': str(FAIL_STATUS),
                                                         'message': str(USER_ALREADY_BLOCKED)
                                                   }
                                                 ),
                                                 400
                                                )

                    else:
                        users.find_one_and_update({
                                                  "email" : email
                                                },{
                                                  '$set': {
                                                    'is_blocked' : TRUE
                                                  },
                                                })
                        response = make_response(
                                    jsonify(
                                        {
                                            "status": str(SUCCESS_STATUS),
                                            "message": str(USER_BLOCKED_SUCCESSFULLY)
                                        }
                                    ),
                                    201,
                                )

            except Exception as e:
                response = make_response(
                                      jsonify(
                                             {
                                              "status": str(FAIL_STATUS),
                                              "error": str(e)
                                              }
                                              ),
                                         500,
                                     )
        else:
            flash(error)
            response = make_response(
                            jsonify(
                                 {
                                     "status": str(FAIL_STATUS),
                                     "error": str(error)
                                 }
                                ),
                                500,
                               )

    response.headers["Content-Type"] = "application/json"
    return response




@bp.route('/unblock', methods=('GET', 'PATCH'))
@token_required
def unblock():
    if request.method == 'PATCH':
        email = request.form.get('email')
        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
        if error is None:
            try:
                users = db.users
                user = users.find_one({"email":email})

                if user is None:
                    error = EMAIL_NOT_FOUND
                    response = make_response(
                                     jsonify(
                                            {
                                              "status": str(FAIL_STATUS),
                                              "message": str(EMAIL_NOT_FOUND)
                                            }
                                            ),
                                            404,
                                     )


                else:
                    if not user['is_blocked']:
                        response = make_response(
                                              jsonify(
                                                   {
                                                        'status': str(FAIL_STATUS),
                                                         'message': str(USER_ALREADY_UNBLOCKED)
                                                   }
                                                 ),
                                                 400
                                                )

                    else:
                        users.find_one_and_update({
                                                  "email" : email
                                                },{
                                                  '$set': {
                                                    'is_blocked' : FALSE
                                                  },
                                                })
                        response = make_response(
                                    jsonify(
                                        {
                                            "status": str(SUCCESS_STATUS),
                                            "message": str(USER_UNBLOCKED_SUCCESSFULLY)
                                        }
                                    ),
                                    201,
                                )

            except Exception as e:
                response = make_response(
                                      jsonify(
                                             {
                                              "status": str(FAIL_STATUS),
                                              "error": str(e)
                                              }
                                              ),
                                         500,
                                     )
        else:
            flash(error)
            response = make_response(
                                jsonify(
                                    {
                                    "status": str(FAIL_STATUS),
                                    "error": str(error)
                                    }
                                  ),
                                  500,
                                 )

    response.headers["Content-Type"] = "application/json"
    return response




@bp.route('/getAllBlocked', methods=('GET', 'POST'))
@token_required
def getAllBlocked():
    db = get_db()
    users_collection = db.users
    users = users_collection.find({'is_blocked': TRUE},{'email': 1})
    users = [User(**doc).to_json() for doc in users]
    response = make_response(
                        jsonify(
                            {
                               "status": str(SUCCESS_STATUS),
                                "users": users
                            }
                            ),
                            200,
                        )
    response.headers["Content-Type"] = "application/json"
    return response



@bp.route('/getAllUnblocked', methods=('GET', 'POST'))
@token_required
def getAllUnblocked():
    db = get_db()
    users_collection = db.users
    users = users_collection.find({'is_blocked': FALSE},{'email': 1})
    users = [User(**doc).to_json() for doc in users]
    response = make_response(
                        jsonify(
                            {
                               "status": str(SUCCESS_STATUS),
                                "users": users
                            }
                            ),
                            200,
                        )
    response.headers["Content-Type"] = "application/json"
    return response