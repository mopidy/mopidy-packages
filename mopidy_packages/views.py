import flask

from . import app, models


api_endpoints = []


def api_endpoint(func):
    """Decorator for adding a view to the list of public API endpoints"""
    api_endpoints.append(func)
    return func


@app.route('/')
def index():
    return flask.redirect(flask.url_for('list_api_endpoints'))


@app.route('/api')
def list_api_endpoints():
    url_rules = {f.endpoint: f.rule for f in app.url_map.iter_rules()}

    return flask.jsonify(endpoints={
        func.__name__: {
            'url': url_rules[func.__name__],
            'description': func.__doc__,
        }
        for func in api_endpoints
    })


@api_endpoint
@app.route('/api/people')
def list_people():
    """Returns a list of people in the Mopidy community"""

    try:
        people = [p.to_json() for p in models.Person.all()]
    except models.ModelException as exc:
        return flask.Response(str(exc), status=500, content_type='text/plain')

    return flask.jsonify(people=people)


@api_endpoint
@app.route('/api/people/<name>')
def get_person(name):
    """Returns detailed information about a specific person"""

    try:
        person = models.Person.get(name)
    except models.ModelException as exc:
        return flask.Response(str(exc), status=500, content_type='text/plain')

    if person is None:
        flask.abort(404)

    return flask.jsonify(person.to_json())


@api_endpoint
@app.route('/api/projects')
def list_projects():
    """Returns a list of projects in the Mopidy ecosystem"""

    try:
        projects = [p.to_json() for p in models.Project.all()]
    except models.ModelException as exc:
        return flask.Response(str(exc), status=500, content_type='text/plain')

    return flask.jsonify(projects=projects)


@api_endpoint
@app.route('/api/projects/<name>')
def get_project(name):
    """Returns detailed information about a specific project"""

    try:
        project = models.Project.get(name)
    except models.ModelException as exc:
        return flask.Response(str(exc), status=500, content_type='text/plain')

    if project is None:
        flask.abort(404)

    return flask.jsonify(project.to_json())
