import datetime
import distutils.version

from natsort import natsorted

import requests

from mopidy_packages.models import Project


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
