import json


def test_index_redirects_to_api(static_app):
    response = static_app.get('/')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/api/')


def test_path_that_does_not_exist(static_app):
    response = static_app.get('/foo/')

    assert response.status_code == 404


def test_path_returns_correct_file_as_json(static_app, tmpdir):
    index_file = tmpdir.mkdir('foo').join('index.html')
    index_file.write(json.dumps({'foo': 'bar'}))

    response = static_app.get('/foo/')

    assert response.status_code == 200
    assert response.mimetype == 'application/json'

    data = json.loads(response.data.decode('utf-8'))
    assert data == {'foo': 'bar'}
