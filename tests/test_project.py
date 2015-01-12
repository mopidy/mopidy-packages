import json
import pathlib

import responses

from mopidy_packages import models


TEST_DIR = pathlib.Path(__file__).parent
DATA_DIR = TEST_DIR / 'data'


def test_project_with_id():
    project = models.Project(id='foobar')

    assert project.id == 'foobar'
    assert project.path.name == 'project.json'
    assert project.path.parent.name == 'foobar'
    assert project.data is None


def test_project_with_path():
    project = models.Project(path=pathlib.Path('/foobar/project.json'))

    assert project.id is None
    assert project.path.name == 'project.json'
    assert project.path.parent.name == 'foobar'
    assert project.data is None


def test_project_with_data_read_from_file():
    project = models.Project(id='mopidy-spotify')

    assert project.data['name'] == 'Mopidy-Spotify'


def test_project_with_invalid_data_file():
    path = DATA_DIR / 'invalid_project.json'
    try:
        models.Project(path=path)
    except models.ModelException as exc:
        assert 'Invalid JSON structure' in str(exc)


@responses.activate
def test_project_enrich():
    responses.add(
        responses.GET, 'https://api.github.com/repos/mopidy/mopidy-spotify',
        status=404)

    project = models.Project(id='mopidy-spotify')
    project._enrichers = {'distribution.github': models.add_github_repo}

    assert project.data['distribution']['github'] == 'mopidy/mopidy-spotify'

    project.enrich()

    assert project.data['distribution']['github']['owner'] == 'mopidy'


@responses.activate
def test_add_github_repo_with_failing_service():
    responses.add(
        responses.GET, 'https://api.github.com/repos/mopidy/mopidy-spotify',
        status=404)

    data = {'distribution': {'github': 'mopidy/mopidy-spotify'}}

    result = models.add_github_repo(data)

    assert result['id'] == 'mopidy/mopidy-spotify'
    assert result['owner'] == 'mopidy'
    assert result['repo'] == 'mopidy-spotify'
    assert result['url'] == 'https://github.com/mopidy/mopidy-spotify'


@responses.activate
def test_add_github_repo_with_working_service():
    responses.add(
        responses.GET, 'https://api.github.com/repos/mopidy/mopidy-spotify',
        body=json.dumps({
            'created_at': '123',
            'pushed_at': '456',
            'updated_at': '789',
            'description': 'Describing text',
            'homepage': 'www.mopidy.com',
            'language': 'Python',
            'subscribers_count': 21,
            'stargazers_count': 72,
            'forks_count': 22,
            'open_issues_count': 15,
        }),
        status=200, content_type='application/json')
    responses.add(
        responses.GET,
        'https://api.github.com/repos/mopidy/mopidy-spotify/tags',
        body=json.dumps([
            {'name': 'v1.2.0'},
            {'name': 'v1.1.3'},
            {'name': 'debian/v1.2.0-1'},
        ]),
        status=200, content_type='application/json')

    data = {'distribution': {'github': 'mopidy/mopidy-spotify'}}

    result = models.add_github_repo(data)

    assert result['id'] == 'mopidy/mopidy-spotify'
    assert result['created_at'] == '123'
    assert result['pushed_at'] == '456'
    assert result['updated_at'] == '789'
    assert result['description'] == 'Describing text'
    assert result['homepage'] == 'www.mopidy.com'
    assert result['language'] == 'Python'
    assert result['watchers_count'] == 21
    assert result['stargazers_count'] == 72
    assert result['forks_count'] == 22
    assert result['open_issues_count'] == 15
    assert result['tags'] == ['v1.2.0', 'v1.1.3']


def test_add_github_repo_without_input():
    assert models.add_github_repo({'distribution': {}}) is None
