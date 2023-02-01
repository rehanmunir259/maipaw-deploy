import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db
from flask_mail import Mail, Message
from flask import current_app, g, jsonify, make_response
from ..models.model import Package
from random import randrange
import random
import math
import bson.json_util as json_util
from ..models.objectid import PydanticObjectId
from pymongo import ReturnDocument
from ..middlewares.auth_middleware import token_required



bp = Blueprint('package', __name__, url_prefix='/package')

SUCCESS_STATUS = 'Successful'
FAIL_STATUS = 'Failed'
AVATAR_MISSING = 'Number of avatars missing'
VARIATIONS_MISSING = 'Number of variations missing'
STYLES_MISSING = 'Number of styles missing'
PRICE_MISSING = 'Price is missing'
PACKAGE_NOT_FOUND = 'Package not found'
SEND_ID = 'Please send a valid id'
NOTHING_TO_UPDATE = 'Nothing to update'
COULDNT_DELETE = "Couldn't delete package"
PACKAGE_ALREADY_EXISTS = 'Package already exists'

@bp.route('/create', methods=('GET', 'POST'))
@token_required
def create():
    response = ''
    if request.method == 'POST':
        avatars = request.form.get('avatars')
        variations = request.form.get('variations')
        styles = request.form.get('styles')
        price = request.form.get('price')
        db = get_db()
        error = None
        if not avatars:
            error = AVATAR_MISSING

        elif not variations:
            error = VARIATIONS_MISSING

        elif not styles:
            error = STYLES_MISSING

        elif not price:
            error = PRICE_MISSING

        if error is None:
            try:
                packages = db.packages
                existing = packages.find_one({
                                            'avatars': int(avatars),
                                            'variations': int(variations),
                                            'styles': int(styles),
                                            'price': int(price)
                                        })

                if(existing):
                    response = make_response(
                                          jsonify(
                                          {
                                            'status': FAIL_STATUS,
                                            'message': PACKAGE_ALREADY_EXISTS
                                          }
                                          ),
                                          403
                                        )

                else:
                    package = Package(avatars=avatars, variations=variations, styles=styles, price=price)
                    new_package = packages.insert_one(package.to_bson())
                    new_package = packages.find_one({"_id":new_package.inserted_id})
                    new_package = Package(**new_package).to_json()
                    response = make_response(
                                     jsonify(
                                       {
                                          "status": str(SUCCESS_STATUS),
                                          "package": new_package
                                       }
                                       ),
                                      201,
                                     )

            except Exception as e:
                response = make_response(
                                   jsonify(
                                     {
                                       error: str(e)
                                     }
                                     ),
                                     500,
                                    )
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

#     response.headers["Content-Type"] = "application/json"
    return response



@bp.route('/getAll', methods=('GET', 'POST'))
def getAll():
    response = ''
    db = get_db()
    error = None
    collection = db.packages
    packages = collection.find().sort('price',1)
    packages = [Package(**doc).to_json() for doc in packages]
    response = make_response(
                        jsonify(
                            {
                               "status": str(SUCCESS_STATUS),
                                "packages": packages
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
    print('-------------')
    print(id)
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
        collection = db.packages
        id = PydanticObjectId(id)
        package = collection.find_one({'_id':id})
        print('----------------')
        print(package)
        if not package:
            response = make_response(
                               jsonify({
                                         "status": str(FAIL_STATUS),
                                          "message": str(PACKAGE_NOT_FOUND)
                                     }),
                                 404
                             )
            response.headers["Content-Type"] = "application/json"
            return response

        package = Package(**package).to_json()

        response = make_response(
                            jsonify(
                                {
                                   "status": str(SUCCESS_STATUS),
                                    "packages": package
                                }
                                ),
                                200,
                            )
        response.headers["Content-Type"] = "application/json"
        return response






@bp.route('/update', methods=('GET', 'PATCH'))
@token_required
def update():
    response = ''
    if request.method == 'PATCH':
        avatars = request.form.get('avatars')
        variations = request.form.get('variations')
        styles = request.form.get('styles')
        price = request.form.get('price')
        id = request.form.get('id')
        db = get_db()
        error = None

        if not id:
            error = SEND_ID

        elif not avatars and not variations and not styles and not price:
            error = NOTHING_TO_UPDATE

        if error is None:
            try:
                collection = db.packages

                old_package = collection.find_one({'_id': PydanticObjectId(id)})
                if not old_package:
                    response = make_response(
                               jsonify({
                                         "status": str(FAIL_STATUS),
                                          "message": str(PACKAGE_NOT_FOUND)
                                     }),
                                 404
                             )
                else:
                    package = collection.find_one_and_update({
                              '_id': PydanticObjectId(id)
                            },{
                              '$set': {
                                'avatars' : avatars if avatars else old_package['avatars'],
                                'variations': variations if variations else old_package['variations'],
                                'styles': styles if styles else old_package['styles'] ,
                                'price': price if price else old_package['price']
                              },
                            }, return_document = ReturnDocument.AFTER)

                    package = Package(**package).to_json()
                    response = make_response(
                                 jsonify(
                                   {
                                      "status": str(SUCCESS_STATUS),
                                      "package": package
                                   }
                                   ),
                                  201,
                                 )

            except Exception as e:
                response = make_response(
                                   jsonify(
                                     {
                                       error: str(e)
                                     }
                                     ),
                                     500,
                                    )
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

#     response.headers["Content-Type"] = "application/json"
    return response


@bp.route('/delete', methods=('GET', 'DELETE'))
@token_required
def delete():
    response = ''
    if request.method == 'DELETE':
        id = request.args.get('id')
        db = get_db()
        error = None

        if not id:
            error = SEND_ID

        if error is None:
            try:
                collection = db.packages
                result = collection.delete_one({'_id': PydanticObjectId(id)})
                print(result.deleted_count)
                if(result.deleted_count == 0):
                    response = make_response(
                                                     jsonify(
                                                       {
                                                          "status": str(FAIL_STATUS),
                                                          "message": PACKAGE_NOT_FOUND
                                                       }
                                                       ),
                                                      404,
                                                     )
                    return response

                else:
                    response = make_response(
                                     jsonify(
                                       {
                                          "status": str(SUCCESS_STATUS),
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

#     response.headers["Content-Type"] = "application/json"
    return response

