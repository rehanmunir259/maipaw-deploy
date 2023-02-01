import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db
from flask_mail import Mail, Message
from flask import current_app, g, jsonify, make_response
from ..models.model import Style
from random import randrange
import random
import math
import bson.json_util as json_util
from ..models.objectid import PydanticObjectId
from pymongo import ReturnDocument
from ..middlewares.upload_middleware import upload_file
from ..middlewares.auth_middleware import token_required

bp = Blueprint('style', __name__, url_prefix='/style')

SUCCESS_STATUS = 'Successful'
FAIL_STATUS = 'Failed'
NAME_MISSING = 'Name is missing'
IMAGE_MISSING = 'Image is missing'
STYLE_NOT_FOUND = 'Style not found'
SEND_ID = 'Please send a valid id'
NOTHING_TO_UPDATE = 'Nothing to update'
COULDNT_DELETE = "Couldn't delete package"
IMAGE_TYPE = 'app_image'
STYLE_ALREADY_EXISTS = 'Style already exists'

@bp.route('/create', methods=('GET', 'POST'))
@token_required
def create():
    response = ''
    if request.method == 'POST':
        name = request.form.get('name')
        image = request.files.get('image')
        db = get_db()
        error = None
        if not name:
            error = NAME_MISSING

        elif not image:
            error = IMAGE_MISSING

        if error is None:
            try:
                collection = db.styles
                existing = collection.find_one({
                                            'name': name,
                                        })

                if(existing):
                    response = make_response(
                                          jsonify(
                                          {
                                            'status': FAIL_STATUS,
                                            'message': STYLE_ALREADY_EXISTS
                                          }
                                          ),
                                          403
                                        )

                else:
                    url = upload_file(type=IMAGE_TYPE, file=image)
                    style = Style(name=name, image=url)
                    new_style = collection.insert_one(style.to_bson())
                    new_style = collection.find_one({"_id":new_style.inserted_id})
                    new_style = Style(**new_style).to_json()
                    response = make_response(
                                     jsonify(
                                       {
                                          "status": str(SUCCESS_STATUS),
                                          "style": new_style
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

    response.headers["Content-Type"] = "application/json"
    return response



@bp.route('/getAll', methods=('GET', 'POST'))
def getAll():
    db = get_db()
    error = None
    collection = db.styles
    styles = collection.find().sort('_id',-1)
    styles = [Style(**doc).to_json() for doc in styles]
    response = make_response(
                        jsonify(
                            {
                               "status": str(SUCCESS_STATUS),
                                "styles": styles
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
        collection = db.styles
        id = PydanticObjectId(id)
        style = collection.find_one({'_id':id})
        if not style:
            response = make_response(
                               jsonify({
                                         "status": str(FAIL_STATUS),
                                          "message": str(STYLE_NOT_FOUND)
                                     }),
                                 404
                             )
            response.headers["Content-Type"] = "application/json"
            return response

        style = Style(**style).to_json()

        response = make_response(
                            jsonify(
                                {
                                   "status": str(SUCCESS_STATUS),
                                    "style": style
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
        id = request.form.get('id')
        name = request.form.get('name')
        image = request.files.get('image')
        db = get_db()
        error = None

        if not id:
            error = SEND_ID

        elif not name and not image:
            error = NOTHING_TO_UPDATE

        if error is None:
            try:
                collection = db.styles
                old_style = collection.find_one({'_id': PydanticObjectId(id)})
                if not old_style:
                    response = make_response(
                                    jsonify(
                                         {
                                          "status": str(FAIL_STATUS),
                                          "message": STYLE_NOT_FOUND
                                         }
                                         ),
                                         404,
                                      )

                else:
                    if image:
                        url = upload_file(type=IMAGE_TYPE, file=image)


                    style = collection.find_one_and_update({
                              '_id': PydanticObjectId(id)
                            },{
                              '$set': {
                                'name' : name if name else old_style['name'],
                                'image': url if image else old_style['image'],
                              },
                            }, return_document = ReturnDocument.AFTER)

                    style = Style(**style).to_json()
                    response = make_response(
                                 jsonify(
                                   {
                                      "status": str(SUCCESS_STATUS),
                                      "style": style
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
                collection = db.styles
                old_style = collection.find_one({'_id': PydanticObjectId(id)})
                result = collection.delete_one({'_id': PydanticObjectId(id)})
                if(result.deleted_count == 0):
                    response = make_response(
                                                     jsonify(
                                                       {
                                                          "status": str(FAIL_STATUS),
                                                          "message": STYLE_NOT_FOUND
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

    response.headers["Content-Type"] = "application/json"
    return response

