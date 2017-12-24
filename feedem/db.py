import os

import click
import jsonschema

from . import normalize_path, dump_yaml, YAML
from .log import Logging


class Document(object):
    def __init__(self, db, document_id):
        self._db = db
        self._data = None

        self.document_id = document_id

        self.dirty = False

    def _get_raw(self):
        with click.open_file(self._db.document_path(self.document_id), mode='r', encoding='utf-8') as f:
            return f.read()

    def _set_raw(self, text):
        document_path = self._db.document_path(self.document_id)

        with click.open_file(document_path, mode='w', encoding='utf-8') as f:
            f.write(text)
            f.flush()

        self.data = None

    raw = property(_get_raw, _set_raw)

    def _get_data(self):
        if self._data is None:
            self._data = YAML.load(self.raw)

        return self._data

    def _set_data(self, value):
        self._data = value

    data = property(_get_data, _set_data)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __hasitem__(self, key):
        return key in self.data

    def save(self, force=False):
        if not self.dirty and force is not True:
            return

        assert self._data is not None

        document_path = self._db.document_path(self.document_id)

        dump_yaml(self._data, document_path, logger=self._db.logger)

        self.dirty = False

    @classmethod
    def validate(cls, data, schema):
        try:
            jsonschema.validate(data, schema)
            return True

        except jsonschema.exceptions.ValidationError as exc:
            return exc

    @classmethod
    def new(cls, db, document_id):
        document = cls(db, document_id)
        document.data = {}

        return document

    @classmethod
    def get(cls, db, document_id):
        return cls(db, document_id)


class Index(Document):
    def __init__(self, db, **kwargs):
        super(Index, self).__init__(db, 'index', **kwargs)


class Recipe(Document):
    SCHEMA = {
        'type': 'object',
        'properties': {
            'title': {
                'type': 'string'
            }
        }
    }

    @classmethod
    def validate(cls, data):
        return super(Recipe, cls).validate(data, Recipe.SCHEMA)

    @property
    def preparation_time(self):
        return sum([step.get('time', 0) for step in self['steps']])


class Menu(Document):
    SCHEMA = {
        'type': 'object'
    }

    @classmethod
    def validate(cls, data):
        return super(Menu, cls).validate(data, Menu.SCHEMA)


class DB(object):
    def __init__(self, path, logger=None):
        self.logger = logger or Logging.get_logger()

        self._path = normalize_path(path)
        self._index = None

    @property
    def index(self):
        if self._index is None:
            self._index = Index(self)

        return self._index

    @classmethod
    def initialize(cls, path, logger=None):
        logger = logger or Logging.get_logger()

        if os.path.exists(path):
            logger.debug("directory '{}' exists already".format(path))

        else:
            logger.debug("create directory '{}'".format(path))
            os.mkdir(path)

        db = DB(path)

        index_data = {
            'recipes': [],
            'menus': []
        }

        index = Index(db)
        index.data = index_data
        index.save(force=True)

        return db

    def document_path(self, did):
        return os.path.join(self._path, '{}.yml'.format(did))
