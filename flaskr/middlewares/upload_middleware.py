import functools
import os
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flaskr.db import get_db
from flask import current_app
import uuid
from .. import db
from os.path import join, dirname, realpath


UPLOADS_PATH_FOR_INPUT_IMAGES = join(dirname(realpath(__file__)), '../uploads/input_images/')
UPLOADS_PATH_FOR_OUTPUT_IMAGES = join(dirname(realpath(__file__)), '../uploads/output_images/')
UPLOADS_PATH_FOR_APP_IMAGES = join(dirname(realpath(__file__)), '../uploads/app_images/')


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_file(type, file):
#     file = request.files['file']
#     if file.filename == '':
#         flash('No selected file')
#         return redirect(request.url)
    if file and allowed_file(file.filename):
#         uploading file
        filename = secure_filename(file.filename)
        filename = str(uuid.uuid4()) + '.' + filename.rsplit('.', 1)[1].lower()
        if(type=="input_image"):
            file.save(os.path.join(UPLOADS_PATH_FOR_INPUT_IMAGES,filename))

        if(type=="output_image"):
            file.save(os.path.join(UPLOADS_PATH_FOR_OUTPUT_IMAGES,filename))

        if(type=="app_image"):
            file.save(os.path.join(UPLOADS_PATH_FOR_APP_IMAGES,filename))

#           image processing

#           saving output images


#           send output images back
        return filename

#    return 'file uploaded successfully'


# app = Flask(__name__, template_folder='templateFiles', static_folder='staticFiles')
