import requests

from mopidy_packages.models import Person


@Person.enricher('github')
def add_github_profile(data):
    username = data['profiles'].get('github')
    if username is None:
        return
    return {
        'username': username,
        'url': 'https://github.com/%s' % username,
        'sources': [],
    }


@Person.enricher('twitter')
def add_twitter_profile(data):
    username = data['profiles'].get('twitter')
    if username is None:
        return
    return {
        'username': username,
        'url': 'https://twitter.com/%s' % username,
        'sources': [],
    }


@Person.enricher('discuss')
def add_discuss_profile(data):
    username = data['profiles'].get('discuss')
    if username is None:
        return

    url = 'https://discuss.mopidy.com/users/%s' % username
    result = {
        'username': username,
        'url': url,
        'sources': [],
    }

    api_url = url + '.json'
    response = requests.get(api_url)
    if response.status_code != 200:
        return result

    result['sources'].append(api_url)

    discuss = response.json()
    result['last_posted_at'] = discuss.get('user').get('last_posted_at')
    result['last_seen_at'] = discuss.get('user').get('last_seen_at')
    return result


@Person.enricher('gravatar')
def add_gravatar(data):
    import hashlib
    import urllib.parse

    def gravatar_url(email, size=None, default=None):
        params = {}
        if size is not None:
            params['s'] = str(size)
        if default is not None:
            params['d'] = default

        return (
            'http://www.gravatar.com/avatar/' +
            hashlib.md5(email.lower()).hexdigest() +
            '?' + urllib.parse.urlencode(params)
        )

    email = data.get('email', 'default').encode('utf-8')

    return {
        'base': gravatar_url(email),
        'large': gravatar_url(email, size=460, default='mm'),
        'medium': gravatar_url(email, size=200, default='mm'),
        'small': gravatar_url(email, size=80, default='mm'),
        'sources': [],
    }
