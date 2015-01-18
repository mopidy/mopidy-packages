import json

from mopidy_packages import models


def test_index_redirects_to_api(app):
    response = app.get('/')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/api/')


def test_api_lists_known_api_endpoints(app):
    response = app.get('/api/')

    assert response.status_code == 200

    data = json.loads(response.data.decode('utf-8'))
    endpoints = data['endpoints']

    assert endpoints['list_people']['url'] == '/api/people/'
    assert endpoints['get_person']['url'] == '/api/people/<id>/'
    assert endpoints['list_projects']['url'] == '/api/projects/'
    assert endpoints['get_project']['url'] == '/api/projects/<id>/'


def test_list_people(app):
    response = app.get('/api/people/')

    assert response.status_code == 200

    data = json.loads(response.data.decode('utf-8'))
    people = data['people']
    person = [p for p in people if p['id'] == 'jodal'][0]

    # Static properties
    assert person['name'] == 'Stein Magnus Jodal'
    assert 'email' in person
    assert 'profiles' in person

    # Generated properties
    assert person['url'].endswith('/api/people/jodal/')


def test_list_people_fails(app, models_mock):
    models_mock.Person.all.side_effect = models.ModelException('foo')

    response = app.get('/api/people/')

    assert response.status_code == 500


def test_get_person(app, person_enrich_mock):
    response = app.get('/api/people/jodal/')

    assert response.status_code == 200

    person = json.loads(response.data.decode('utf-8'))

    # Static properties
    assert person['name'] == 'Stein Magnus Jodal'
    assert 'email' in person
    assert 'profiles' in person

    # Generated properties
    assert person['url'].endswith('/api/people/jodal/')

    # Data has been enriched
    person_enrich_mock.assert_called_once_with()


def test_get_person_without_data(app, models_mock):
    models_mock.Person.return_value.data = None

    response = app.get('/api/people/jodal/')

    assert response.status_code == 404


def test_get_person_fails(app, models_mock):
    models_mock.Person.side_effect = models.ModelException('foo')

    response = app.get('/api/people/jodal/')

    assert response.status_code == 500


def test_list_projects(app):
    response = app.get('/api/projects/')

    assert response.status_code == 200

    data = json.loads(response.data.decode('utf-8'))
    projects = data['projects']
    project = [p for p in projects if p['id'] == 'mopidy-spotify'][0]

    # Static properties
    assert project['license'] == 'Apache-2.0'
    assert project['is_extension'] is True

    # Generated properties
    assert project['url'].endswith('/api/projects/mopidy-spotify/')


def test_list_projects_fails(app, models_mock):
    models_mock.Project.all.side_effect = models.ModelException('foo')

    response = app.get('/api/projects/')

    assert response.status_code == 500


def test_get_project(app, project_enrich_mock):
    response = app.get('/api/projects/mopidy-spotify/')

    assert response.status_code == 200

    project = json.loads(response.data.decode('utf-8'))

    # Static properties
    assert project['name'] == 'Mopidy-Spotify'
    assert 'homepage' in project
    assert 'license' in project
    assert 'distribution' in project

    # Generated properties
    assert project['url'].endswith('/api/projects/mopidy-spotify/')

    # Data has been enriched
    project_enrich_mock.assert_called_once_with()


def test_get_project_without_data(app, models_mock):
    models_mock.Project.return_value.data = None

    response = app.get('/api/projects/mopidy-spotify/')

    assert response.status_code == 404


def test_get_project_fails(app, models_mock):
    models_mock.Project.side_effect = models.ModelException('foo')

    response = app.get('/api/projects/mopidy-spotify/')

    assert response.status_code == 500
