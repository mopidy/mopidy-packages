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
            obj = cls(path=path)
            if obj.data is not None:
                yield obj

    def __init__(self, id=None, path=None):
        assert id or path

        if id is not None:
            self.id = id
            self.path = self.DIR / (self.DATA_FORMAT % id)
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
