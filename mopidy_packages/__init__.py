import os

import flask


app = flask.Flask(__name__)
app.config['DEBUG'] = 'DEBUG' in os.environ


from . import models  # noqa: Import models to register them
from . import views  # noqa: Import views to register them
