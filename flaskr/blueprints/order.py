import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db
from flask_mail import Mail, Message
from flask import current_app, g, jsonify, make_response
from ..models.model import Order, Package, Style
from random import randrange
import random
import math
import bson.json_util as json_util
from ..models.objectid import PydanticObjectId
from pymongo import ReturnDocument
from ..middlewares.upload_middleware import upload_file
import datetime
from ..middlewares.auth_middleware import token_required
from bson.json_util import dumps, loads

bp = Blueprint('order', __name__, url_prefix='/order')

SUCCESS_STATUS = 'Successful'
FAIL_STATUS = 'Failed'
USER_ID_MISSING = 'User id missing'
PACKAGE_ID_MISSING = 'Package id is missing'
STYLES_MISSING = 'Styles missing'
INPUT_IMAGES_MISSING = 'Input images missing'
PACKAGE_NOT_FOUND = 'Package not found'
USER_NOT_FOUND = 'User not found'
ORDER_NOT_FOUND = 'Order not found'
STYLE_NOT_FOUND = 'Style not found'
SEND_ID = 'Please send a valid id'
IN_PROCESS = 'In-Process'
USER_BLOCKED = 'User is blocked'

@bp.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        package_id = request.form.get('package_id')
        style_ids = request.form.get('styles')
        input_images = request.files.getlist('images')

        db = get_db()
        error = None
        orders_collection = db.orders
        packages_collection = db.packages
        styles_collection = db.styles
        users_collection = db.users
        if not user_id:
            error = USER_ID_MISSING

        elif not package_id:
            error = PACKAGE_ID_MISSING

        elif style_ids is None:
            error = STYLES_MISSING

        elif not input_images:
            error = INPUT_IMAGES_MISSING

        new_style_ids=[]

        if style_ids:
            style_ids = style_ids.split(',')
            for style_id in style_ids:
                new_style_ids.append(PydanticObjectId(style_id))

            for style in new_style_ids:
                existing = styles_collection.find_one({'_id': style})
                if not existing:
                    error = STYLE_NOT_FOUND

        package = packages_collection.find_one({'_id':PydanticObjectId(package_id)})
        user = users_collection.find_one({'_id':PydanticObjectId(user_id)})

        if package_id and not package:
            error = PACKAGE_NOT_FOUND

        if user_id and not user:
            print(user_id)
            error = USER_NOT_FOUND

        if user and user['is_blocked']:
            error = USER_BLOCKED

        if error is None:
            try:
                package = Package(**package)

                style_list = []
                styles = styles_collection.find({
                                            '_id': {
                                                '$in': new_style_ids
                                            }
                                        })
                for doc in styles:
                    style_list.append(Style(**doc))

                images_urls = []
                for image in input_images:
                    images_urls.append(upload_file(type='input_image', file=image))

                last_modified = datetime.datetime.utcnow()
                status= IN_PROCESS
                order = Order(user_id=user_id, package=package, styles=style_list, input_images=images_urls, last_modified=last_modified, status=status)
                new_order = orders_collection.insert_one(order.to_bson()).inserted_id
                new_order = orders_collection.find_one({'_id':new_order})
                new_order = Order(**new_order).to_json()

                response = make_response(
                                 jsonify(
                                   {
                                      "status": str(SUCCESS_STATUS),
                                      'order': new_order

                                   }
                                   ),
                                  201,
                                 )
                return response

            except Exception as e:
                response = make_response(
                                   jsonify(
                                     {
                                       error: str(e)
                                     }
                                     ),
                                     500,
                                    )
                return response
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
            return response
        flash(error)

    response.headers["Content-Type"] = "application/json"
    return response



@bp.route('/getAll', methods=('GET', 'POST'))
@token_required
def getAll():
    response = ''
    db = get_db()
    error = None
    collection = db.orders

    orders = collection.aggregate([
                                    {
                                        '$lookup': {
                                            'from': 'users',
                                            'localField': 'user_id',
                                            'foreignField': '_id',
                                            'as': 'user',
                                            'pipeline': [
                                            {
                                                '$project': {
                                                    '_id': 1,
                                                    'email': 1
                                                }
                                            }

                                            ]
                                        }
                                      },
                                      {
                                        '$sort': {
                                            '_id': -1
                                        }
                                      },
                                      {
                                        '$project': {
                                            'user_id': 0
                                        }
                                      }
                                    ])

    orders = [Order(**doc).to_json() for doc in orders]
    response = make_response(
                        jsonify(
                            {
                               "status": str(SUCCESS_STATUS),
                                "orders": orders
                            }
                            ),
                            200,
                        )
    response.headers["Content-Type"] = "application/json"
    return response



@bp.route('/getById', methods=('GET', 'POST'))
def getById():
    response = ''
    id = request.args.get('id')
    db = get_db()
    error = None
    if not id:
        response = make_response(
                                jsonify({
                                        "status": str(FAIL_STATUS),
                                        "message": str(SEND_ID)
                                }),
                                404
                          )
        response.headers["Content-Type"] = "application/json"
        return response

    else:
        collection = db.orders
        id = PydanticObjectId(id)

        order = collection.aggregate([
                                      {
                                        '$match': {
                                            '_id': id
                                        },
                                      },
                                      {
                                        '$lookup': {
                                            'from': 'users',
                                            'localField': 'user_id',
                                            'foreignField': '_id',
                                            'as': 'user',
                                            'pipeline': [
                                            {
                                                '$project': {
                                                    '_id': 1,
                                                    'email': 1
                                                }
                                            }

                                            ]
                                        }
                                      },
                                      {
                                            '$project': {
                                            'user_id': 0
                                      }
                                     }
                                    ])

        order = [Order(**doc).to_json() for doc in order]

        order = order[0]

        if not order:
            response = make_response(
                               jsonify({
                                         "status": str(FAIL_STATUS),
                                          "message": str(ORDER_NOT_FOUND)
                                     }),
                                 404
                             )
            response.headers["Content-Type"] = "application/json"
            return response

        order = Order(**order).to_json()

        response = make_response(
                            jsonify(
                                {
                                   "status": str(SUCCESS_STATUS),
                                    "order": order
                                }
                                ),
                                200,
                            )
        response.headers["Content-Type"] = "application/json"
        return response



@bp.route('/getOrdersOfAUser', methods=('GET', 'POST'))
def getOrdersOfAUser():
    response = ''
    id = request.args.get('user')
    db = get_db()
    error = None
    if not id:
        response = make_response(
                                jsonify({
                                        "status": str(FAIL_STATUS),
                                        "message": str(SEND_ID)
                                }),
                                404
                          )
        response.headers["Content-Type"] = "application/json"
        return response

    else:
        collection = db.orders
        users_collection = db.users
        id = PydanticObjectId(id)
        user = users_collection.find_one({'_id': id})
        if not user:
            response = make_response(
                             jsonify({
                               "status": str(FAIL_STATUS),
                               "message": str(USER_NOT_FOUND)
                            }),
                           404
                        )
            response.headers["Content-Type"] = "application/json"
            return response
        orders = collection.find({'user_id':id}).sort('_id', -1)

        if not orders:
            response = make_response(
                               jsonify({
                                         "status": str(FAIL_STATUS),
                                          "message": str(ORDER_NOT_FOUND)
                                     }),
                                 404
                             )
            response.headers["Content-Type"] = "application/json"
            return response

        orders = [Order(**doc).to_json() for doc in orders]

        response = make_response(
                            jsonify(
                                {
                                   "status": str(SUCCESS_STATUS),
                                    "orders": orders
                                }
                                ),
                                200,
                            )
        response.headers["Content-Type"] = "application/json"
        return response



