import json

import responses

from mopidy_packages import models


def test_add_github_profile():
    data = {'profiles': {'github': 'alice'}}

    result = models.add_github_profile(data)

    assert result['username'] == 'alice'
    assert result['url'] == 'https://github.com/alice'
    assert result['sources'] == []


def test_add_github_profile_without_input():
    assert models.add_github_profile({'profiles': {}}) is None


def test_add_twitter_profile():
    data = {'profiles': {'twitter': 'alice'}}

    result = models.add_twitter_profile(data)

    assert result['username'] == 'alice'
    assert result['url'] == 'https://twitter.com/alice'
    assert result['sources'] == []


def test_add_twitter_profile_without_input():
    assert models.add_twitter_profile({'profiles': {}}) is None


@responses.activate
def test_add_discuss_profile_with_working_service():
    responses.add(
        responses.GET, 'https://discuss.mopidy.com/users/alice.json',
        body=json.dumps({'user': {
            'last_posted_at': '123',
            'last_seen_at': '456',
        }}),
        status=200, content_type='application/json')

    data = {'profiles': {'discuss': 'alice'}}

    result = models.add_discuss_profile(data)

    assert result['username'] == 'alice'
    assert result['url'] == 'https://discuss.mopidy.com/users/alice'
    assert result['last_posted_at'] == '123'
    assert result['last_seen_at'] == '456'
    assert result['sources'] == ['https://discuss.mopidy.com/users/alice.json']


@responses.activate
def test_add_discuss_profile_with_failing_service():
    responses.add(
        responses.GET, 'https://discuss.mopidy.com/users/alice.json',
        status=404)

    data = {'profiles': {'discuss': 'alice'}}

    result = models.add_discuss_profile(data)

    assert result['username'] == 'alice'
    assert result['url'] == 'https://discuss.mopidy.com/users/alice'
    assert result['sources'] == []


def test_add_discuss_profile_without_input():
    assert models.add_discuss_profile({'profiles': {}}) is None


def test_add_gravatar():
    data = {'email': 'alice@example.com'}

    result = models.add_gravatar(data)

    assert result['base'] == (
        'http://www.gravatar.com/avatar/c160f8cc69a4f0bf2b0362752353d060?')
    assert result['sources'] == []

    for k, v in {'small': 80, 'medium': 200, 'large': 460}.items():
        assert result[k].startswith(
            'http://www.gravatar.com/avatar/c160f8cc69a4f0bf2b0362752353d060?')
        assert 'd=mm' in result[k]
        assert 's=%d' % v in result[k]
