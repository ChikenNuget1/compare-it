from flask import Flask, render_template

def create_app():
    app = Flask(__name__)

    with app.app_context():
        from .api import app as compare
        app.register_blueprint(compare.compare_bp)

    return app