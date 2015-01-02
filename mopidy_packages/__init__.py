import os

import flask
from flask.ext.sqlalchemy import SQLAlchemy


app = flask.Flask(__name__)
app.config['DEBUG'] = 'DEBUG' in os.environ
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

db = SQLAlchemy(app)


from . import models  # noqa: Import models to register them
from . import views  # noqa: Import views to register them
