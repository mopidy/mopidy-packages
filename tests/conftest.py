from unittest import mock

import pytest

from mopidy_packages import models, web


@pytest.fixture
def app():
    return web.app.test_client()


@pytest.yield_fixture
def models_mock():
    patcher = mock.patch.object(web, 'models', spec=models)
    models_mock = patcher.start()
    models_mock.ModelException = models.ModelException
    yield models_mock
    patcher.stop()


@pytest.yield_fixture
def person_enrich_mock():
    patcher = mock.patch.object(models.Person, 'enrich')
    yield patcher.start()
    patcher.stop()


@pytest.yield_fixture
def project_enrich_mock():
    patcher = mock.patch.object(models.Project, 'enrich')
    yield patcher.start()
    patcher.stop()
