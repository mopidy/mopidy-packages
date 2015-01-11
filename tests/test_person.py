import json
import pathlib

import responses

from mopidy_packages import models


TEST_DIR = pathlib.Path(__file__).parent
DATA_DIR = TEST_DIR / 'data'


def test_person_with_id():
    person = models.Person(id='alice')

    assert person.id == 'alice'
    assert person.path.name == 'alice.json'
    assert person.path.parent.name == 'people'
    assert person.data is None


def test_person_with_path():
    person = models.Person(path=pathlib.Path('/foo/bar.json'))

    assert person.id is None
    assert person.path.name == 'bar.json'
    assert person.path.parent.name == 'foo'
    assert person.data is None


def test_person_with_data_read_from_file():
    person = models.Person(id='jodal')

    assert person.data['email'] == 'stein.magnus@jodal.no'


def test_person_with_invalid_data_file():
    path = DATA_DIR / 'invalid_person.json'
    try:
        models.Person(path=path)
    except models.ModelException as exc:
        assert 'Invalid JSON structure' in str(exc)


def test_person_enrich():
    person = models.Person(id='jodal')
    person._enrichers = {'github': models.add_github_profile}

    assert person.data['github'] == 'jodal'

    person.enrich()

    assert person.data['github']['username'] == 'jodal'
    assert person.data['github']['url'] == 'https://github.com/jodal'


def test_add_github_profile():
    data = {'github': 'alice'}

    result = models.add_github_profile(data)

    assert result['username'] == 'alice'
    assert result['url'] == 'https://github.com/alice'


def test_add_github_profile_without_input():
    assert models.add_github_profile({}) is None


def test_add_twitter_profile():
    data = {'twitter': 'alice'}

    result = models.add_twitter_profile(data)

    assert result['username'] == 'alice'
    assert result['url'] == 'https://twitter.com/alice'


def test_add_twitter_profile_without_input():
    assert models.add_twitter_profile({}) is None


@responses.activate
def test_add_discuss_profile():
    responses.add(
        responses.GET, 'https://discuss.mopidy.com/users/alice.json',
        body=json.dumps({'user': {
            'last_posted_at': '123',
            'last_seen_at': '456',
        }}),
        status=200, content_type='application/json')

    data = {'discuss': 'alice'}

    result = models.add_discuss_profile(data)

    assert result['username'] == 'alice'
    assert result['url'] == 'https://discuss.mopidy.com/users/alice'
    assert result['last_posted_at'] == '123'
    assert result['last_seen_at'] == '456'


@responses.activate
def test_add_discuss_profile_with_failing_service():
    responses.add(
        responses.GET, 'https://discuss.mopidy.com/users/alice.json',
        status=404)

    data = {'discuss': 'alice'}

    result = models.add_discuss_profile(data)

    assert result['username'] == 'alice'
    assert result['url'] == 'https://discuss.mopidy.com/users/alice'
    assert result['last_posted_at'] is None
    assert result['last_seen_at'] is None


def test_add_discuss_profile_without_input():
    assert models.add_discuss_profile({}) is None


def test_add_gravatar():
    data = {'email': 'alice@example.com'}

    result = models.add_gravatar(data)

    assert result['base'] == (
        'http://www.gravatar.com/avatar/c160f8cc69a4f0bf2b0362752353d060?')

    for k, v in {'small': 80, 'medium': 200, 'large': 460}.items():
        assert result[k].startswith(
            'http://www.gravatar.com/avatar/c160f8cc69a4f0bf2b0362752353d060?')
        assert 'd=mm' in result[k]
        assert 's=%d' % v in result[k]
