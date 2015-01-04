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
    def all(cls):
        for path in cls.DIR.glob(cls.DATA_GLOB):
            if path == cls.SCHEMA_FILE:
                continue
            data = cls._get_data(path)
            if data is None:
                continue
            yield cls(data)

    @classmethod
    def get(cls, name):
        path = cls.DIR / (cls.DATA_FORMAT % name)
        data = cls._get_data(path)
        if data is None:
            return None
        return cls(data)

    @classmethod
    def _get_data(cls, path):
        if not path.exists():
            return None

        with path.open() as fh:
            data = json.load(fh)

        try:
            jsonschema.validate(
                data, cls._get_schema(),
                format_checker=jsonschema.FormatChecker())
        except jsonschema.ValidationError as exc:
            raise ModelException('Invalid JSON structure: %s' % exc) from exc
        else:
            return data

    @classmethod
    def _get_schema(cls):
        if cls._schema_cache is None:
            with cls.SCHEMA_FILE.open() as fh:
                cls._schema_cache = json.load(fh)
        return cls._schema_cache

    def __init__(self, data):
        self.data = data

    def to_json(self):
        return self.data


class Person(Model):
    DIR = ROOT_DIR / 'people'
    DATA_GLOB = '*.json'
    DATA_FORMAT = '%s.json'
    SCHEMA_FILE = DIR / 'person.schema.json'


class Project(Model):
    DIR = ROOT_DIR / 'projects'
    DATA_GLOB = '*/project.json'
    DATA_FORMAT = '%s/project.json'
    SCHEMA_FILE = DIR / 'projects.schema.json'
