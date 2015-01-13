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
    assert result['sources'] == []


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
    assert result['latest_tag'] == 'v1.2.0'
    assert result['sources'] == [
        'https://api.github.com/repos/mopidy/mopidy-spotify',
        'https://api.github.com/repos/mopidy/mopidy-spotify/tags',
    ]


def test_add_github_repo_without_input():
    assert models.add_github_repo({'distribution': {}}) is None


@responses.activate
def test_add_pypi_info_with_failing_service():
    responses.add(
        responses.GET, 'https://pypi.python.org/pypi/Mopidy-Spotify/json',
        status=404)

    data = {'distribution': {'pypi': 'Mopidy-Spotify'}}

    result = models.add_pypi_info(data)

    assert result['id'] == 'Mopidy-Spotify'
    assert result['url'] == 'https://pypi.python.org/pypi/Mopidy-Spotify'
    assert result['sources'] == []


@responses.activate
def test_add_pypi_info_with_working_service():
    responses.add(
        responses.GET, 'https://pypi.python.org/pypi/Mopidy-Spotify/json',
        body=json.dumps({
            'info': {
                'author': 'Stein Magnus Jodal',
                'author_email': 'stein.magnus@jodal.no',
                'version': '1.2.0',
                'downloads': {
                    'last_month': 1695,
                    'last_week': 608,
                    'last_day': 50,
                },
                'requires_dist': [
                    'Pykka (>=1.1)',
                    'Mopidy (>=0.18)',
                ],
            },
            'releases': {
                '1.1.1': {},
                '1.1.0': {},
                '1.2.0': {},
            },
            'urls': [
                {
                    'upload_time': '2014-07-21T00:04:04',
                    'packagetype': 'sdist'
                },
                {
                    'upload_time': '2014-08-03T13:15:45',
                    'packagetype': 'bdist_wheel'
                },
            ]
        }),
        status=200, content_type='application/json')

    data = {'distribution': {'pypi': 'Mopidy-Spotify'}}

    result = models.add_pypi_info(data)

    assert result['id'] == 'Mopidy-Spotify'
    assert result['url'] == 'https://pypi.python.org/pypi/Mopidy-Spotify'
    assert result['author'] == 'Stein Magnus Jodal'
    assert result['author_email'] == 'stein.magnus@jodal.no'
    assert result['version'] == '1.2.0'
    assert result['released_at'] == '2014-07-21T00:04:04Z'
    assert result['downloads'] == {
        'last_month': 1695,
        'last_week': 608,
        'last_day': 50,
    }
    assert result['requires_dist'] == ['Pykka (>=1.1)', 'Mopidy (>=0.18)']
    assert result['has_wheel'] is True
    assert result['releases'] == ['1.2.0', '1.1.1', '1.1.0']
    assert result['sources'] == [
        'https://pypi.python.org/pypi/Mopidy-Spotify/json',
    ]


def test_add_pypi_info_without_input():
    assert models.add_pypi_info({'distribution': {}}) is None


@responses.activate
def test_add_aur_info_with_failing_service():
    responses.add(
        responses.GET,
        'https://aur.archlinux.org/rpc.php?type=info&arg=mopidy-spotify',
        match_querystring=True, status=404)

    data = {'distribution': {'aur': 'mopidy-spotify'}}

    result = models.add_aur_info(data)

    assert result['id'] == 'mopidy-spotify'
    assert result['url'] == (
        'https://aur.archlinux.org/packages/mopidy-spotify/')
    assert result['sources'] == []


@responses.activate
def test_add_aur_info_with_working_service():
    responses.add(
        responses.GET,
        'https://aur.archlinux.org/rpc.php?type=info&arg=mopidy-spotify',
        match_querystring=True,
        body=json.dumps({
            'results': {
                'Description': 'Some text',
                'URL': 'http://www.mopidy.com',
                'Version': '1.2.0-1',
                'OutOfDate': 0,
                'NumVotes': 17,
                'Maintainer': 'AlexandrePTJ',
                'FirstSubmitted': 1382966658,
                'LastModified': 1405946340,
            }
        }),
        status=200, content_type='application/json')

    data = {'distribution': {'aur': 'mopidy-spotify'}}

    result = models.add_aur_info(data)

    assert result['id'] == 'mopidy-spotify'
    assert result['url'] == (
        'https://aur.archlinux.org/packages/mopidy-spotify/')
    assert result['description'] == 'Some text'
    assert result['homepage'] == 'http://www.mopidy.com'
    assert result['version'] == '1.2.0-1'
    assert result['outdated'] is False
    assert result['vote_count'] == 17
    assert result['maintainer'] == 'AlexandrePTJ'
    assert result['created_at'] == '2013-10-28T13:24:18Z'
    assert result['updated_at'] == '2014-07-21T12:39:00Z'
    assert result['sources'] == [
        'https://aur.archlinux.org/rpc.php?type=info&arg=mopidy-spotify',
    ]


def test_add_aur_info_without_input():
    assert models.add_aur_info({'distribution': {}}) is None
