import os
from os.path import join, dirname, realpath

UPLOADS_PATH_FOR_INPUT_IMAGES = join(dirname(realpath(__file__)), '../uploads/input_images/')
UPLOADS_PATH_FOR_OUTPUT_IMAGES = join(dirname(realpath(__file__)), '../uploads/output_images/')
UPLOADS_PATH_FOR_APP_IMAGES = join(dirname(realpath(__file__)), '../uploads/app_images/')


def delete_image(type, name):
    if(type=="input_image"):
        os.remove(UPLOADS_PATH_FOR_INPUT_IMAGES+name)

    if(type=="output_image"):
        os.remove(UPLOADS_PATH_FOR_OUTPUT_IMAGES+name)

    if(type=="app_image"):
        os.remove(UPLOADS_PATH_FOR_APP_IMAGES+name)
