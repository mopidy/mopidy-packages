import pathlib

import flask


app = flask.Flask(__name__)


@app.route('/')
def index():
    return flask.redirect(flask.url_for('dir', path='api'))


@app.route('/<path:path>/')
def dir(path):
    file_path = pathlib.Path(app.config['SITE_DIR']) / path / 'index.html'

    if not file_path.exists():
        flask.abort(404)

    with file_path.open('r') as fh:
        return flask.Response(
            response=fh.read(), status=200, mimetype='application/json')
