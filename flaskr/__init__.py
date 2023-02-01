import os
from os.path import join, dirname, realpath
from flask import Flask
from .role import add_roles

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True, static_folder='uploads')
    UPLOADS_PATH_FOR_INPUT_IMAGES = join(dirname(realpath(__file__)), 'uploads/input_images/')
    UPLOADS_PATH_FOR_OUTPUT_IMAGES = join(dirname(realpath(__file__)), 'uploads/output_images/')
    UPLOADS_PATH_FOR_APP_IMAGES = join(dirname(realpath(__file__)), 'uploads/app_images/')
    app.config['UPLOADS_PATH_FOR_INPUT_IMAGES'] = UPLOADS_PATH_FOR_INPUT_IMAGES
    app.config['UPLOADS_PATH_FOR_OUTPUT_IMAGES'] = UPLOADS_PATH_FOR_OUTPUT_IMAGES
    app.config['UPLOADS_PATH_FOR_APP_IMAGES'] = UPLOADS_PATH_FOR_APP_IMAGES

    app.config['MAIL_SERVER']='smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = 'mockemails135@gmail.com'
    app.config['MAIL_PASSWORD'] = 'npsyrrmsqgcyxszc'
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['SECRET_KEY'] = 'maipawjwt21234'

    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
#     try:
#         os.makedirs(app.instance_path)
#     except OSError:
#         pass

    # a simple page that says hello
    @app.route('/')
    def hello():
        return 'Hello, World!'


    from .blueprints import auth
    app.register_blueprint(auth.bp)

#     from .blueprints import uploads
#     app.register_blueprint(uploads.bp)


    from .blueprints import package
    app.register_blueprint(package.bp)

    from .blueprints import style
    app.register_blueprint(style.bp)

    from .blueprints import order
    app.register_blueprint(order.bp)

    from .blueprints import test
    app.register_blueprint(test.bp)

    from .role import add_roles
#     add_roles()

    from .blueprints import test


    @app.before_first_request
    def before_first_request():
        add_roles()

    return app