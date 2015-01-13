import json
import logging
import pathlib

import jsonschema


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


from mopidy_packages.person import *  # noqa: Register Person enrichers
from mopidy_packages.project import *  # noqa: Register Project enrichers
