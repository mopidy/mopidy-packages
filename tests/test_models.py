import pathlib

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

    assert person.data['profiles']['github'] == 'jodal'
    assert 'updated_at' not in person.data

    person.enrich()

    assert person.data['github']['username'] == 'jodal'
    assert person.data['github']['url'] == 'https://github.com/jodal'
    assert 'updated_at' in person.data


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
