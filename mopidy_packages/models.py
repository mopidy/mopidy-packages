import datetime
import distutils.version
import json
import logging
import pathlib

import jsonschema

from natsort import natsorted

import requests


logger = logging.getLogger(__name__)


ROOT_DIR = pathlib.Path(__file__).parent.parent


class ModelException(Exception):
    pass


class Model:
    _schema_cache = None

    @classmethod
    def enricher(cls, key):
        def inner(func):
            cls._enrichers[key] = func
            return func
        return inner

    @classmethod
    def all(cls):
        for path in cls.DATA_DIR.glob(cls.DATA_GLOB):
            obj = cls(path=path)
            if obj.data is not None:
                yield obj

    def __init__(self, id=None, path=None):
        assert id or path

        if id is not None:
            self.id = id
            self.path = self.DATA_DIR / (self.DATA_FORMAT % id)
        else:
            self.id = None
            self.path = path

        self.data = self._get_data(self.path)

    def _get_data(self, path):
        if not path.exists():
            return None

        with path.open() as fh:
            data = json.load(fh)

        try:
            jsonschema.validate(
                data, self.get_schema(),
                format_checker=jsonschema.FormatChecker())
        except jsonschema.ValidationError as exc:
            raise ModelException('Invalid JSON structure: %s' % exc) from exc
        else:
            return data

    @classmethod
    def get_schema(cls):
        if cls._schema_cache is None:
            with cls.SCHEMA_FILE.open() as fh:
                cls._schema_cache = json.load(fh)
        return cls._schema_cache

    def enrich(self):
        for key, enricher in self._enrichers.items():
            obj = self.data
            parts = key.split('.')
            parts, last = parts[:-1], parts[-1]
            for part in parts:
                obj = obj[part]
            obj[last] = enricher(self.data)


class Person(Model):
    DATA_DIR = ROOT_DIR / 'data' / 'people'
    DATA_GLOB = '*.json'
    DATA_FORMAT = '%s.json'
    SCHEMA_FILE = ROOT_DIR / 'schemas' / 'person.schema.json'

    _enrichers = {}


class Project(Model):
    DATA_DIR = ROOT_DIR / 'data' / 'projects'
    DATA_GLOB = '*/project.json'
    DATA_FORMAT = '%s/project.json'
    SCHEMA_FILE = ROOT_DIR / 'schemas' / 'projects.schema.json'

    _enrichers = {}


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


@Project.enricher('github')
def add_github_repo(data):
    id = data['distribution'].get('github')
    if id is None:
        return

    owner, repo = id.split('/', 1)
    result = {
        'id': id,
        'owner': owner,
        'repo': repo,
        'url': 'https://github.com/%s' % id,
        'sources': [],
    }

    api_url = 'https://api.github.com/repos/%s' % id
    response = requests.get(api_url)
    if response.status_code != 200:
        return result

    result['sources'].append(api_url)

    github = response.json()
    result['created_at'] = github['created_at']
    result['pushed_at'] = github['pushed_at']
    result['updated_at'] = github['updated_at']
    result['description'] = github['description']
    result['homepage'] = github['homepage']
    result['language'] = github['language']
    result['watchers_count'] = github['subscribers_count']
    result['stargazers_count'] = github['stargazers_count']
    result['forks_count'] = github['forks_count']
    result['open_issues_count'] = github['open_issues_count']

    result['tags'] = list(get_github_tags(id))
    result['latest_tag'] = result['tags'] and result['tags'][0] or None
    result['sources'].append(api_url + '/tags')

    return result


def get_github_tags(id):
    response = requests.get('https://api.github.com/repos/%s/tags' % id)
    if response.status_code != 200:
        return

    for tag_obj in response.json():
        tag = tag_obj['name']
        try:
            distutils.version.StrictVersion(tag.lstrip('v'))
        except ValueError:
            continue
        else:
            yield tag


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


@Project.enricher('pypi')
def add_pypi_info(data):
    id = data['distribution'].get('pypi')
    if id is None:
        return

    url = 'https://pypi.python.org/pypi/%s' % id
    result = {
        'id': id,
        'url': url,
        'sources': [],
    }

    api_url = url + '/json'
    response = requests.get(api_url)
    if response.status_code != 200:
        return result

    result['sources'].append(api_url)

    pypi = response.json()
    result['author'] = pypi['info']['author']
    result['author_email'] = pypi['info']['author_email']
    result['version'] = pypi['info']['version']
    result['downloads'] = pypi['info']['downloads']
    result['requires_dist'] = pypi['info']['requires_dist']
    result['has_wheel'] = any(
        url['packagetype'] == 'bdist_wheel' for url in pypi['urls'])

    result['releases'] = list(reversed(natsorted(pypi['releases'].keys())))

    if pypi['urls']:
        result['released_at'] = '%sZ' % pypi['urls'][0]['upload_time']
    else:
        result['released_at'] = None

    return result


@Project.enricher('aur')
def add_aur_info(data):
    id = data['distribution'].get('aur')
    if id is None:
        return

    result = {
        'id': id,
        'url': 'https://aur.archlinux.org/packages/%s/' % id,
        'sources': [],
    }

    api_url = 'https://aur.archlinux.org/rpc.php?type=info&arg=%s' % id
    response = requests.get(api_url)
    if response.status_code != 200:
        return result

    result['sources'].append(api_url)

    aur = response.json()
    result['description'] = aur['results']['Description']
    result['homepage'] = aur['results']['URL']
    result['version'] = aur['results']['Version']
    result['outdated'] = bool(aur['results']['OutOfDate'])
    result['vote_count'] = aur['results']['NumVotes']
    result['maintainer'] = aur['results']['Maintainer']
    result['created_at'] = unix_to_iso(aur['results']['FirstSubmitted'])
    result['updated_at'] = unix_to_iso(aur['results']['LastModified'])

    return result


def unix_to_iso(unix):
    return (
        datetime.datetime
        .utcfromtimestamp(unix)
        .strftime('%Y-%m-%dT%H:%M:%SZ'))


@Project.enricher('apt')
def add_apt_info(data):
    id = data['distribution'].get('apt')
    if id is None:
        return

    result = {
        'id': id,
        'sources': [],
    }

    api_url = 'http://sources.debian.net/api/src/%s/' % id
    response = requests.get(api_url)
    if response.status_code != 200:
        return result

    apt = response.json()
    if 'error' in apt:
        return result

    result['sources'].append(api_url)

    result['suites'] = {}
    for version in apt['versions']:
        for suite in version['suites']:
            result['suites'].setdefault(suite, {})
            result['suites'][suite]['version'] = version['version']

    return result
