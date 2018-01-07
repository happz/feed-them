import os.path
import ruamel.yaml

from .log import Logging, log_dict


YAML = ruamel.yaml.YAML()
YAML.indent(sequence=4, mapping=4, offset=2)

UNITS = {}


def normalize_path(path, fine_if_missing=False, logger=None):
    if not path:
        raise Exception("Path is not valid: '{}'".format(path))

    logger = logger or Logging.get_logger()

    real_path = os.path.expanduser(path)

    if not os.path.exists(real_path) and fine_if_missing is not True:
        raise Exception("Path '{}' does not exist".format(path))

    return real_path


def load_yaml(path, logger=None):
    logger = logger or Logging.get_logger()

    real_path = normalize_path(path, logger=logger)

    logger.debug("loading YAML from '{}' (maps to '{}')".format(path, real_path))

    try:
        with open(real_path, 'r') as f:
            data = YAML.load(f)
            log_dict(logger.debug, "loaded YAML data from '{}'".format(path), data)

            return data

    except ruamel.yaml.YAMLError as exc:
        raise Exception("Unable to load YAML file '{}': {}".format(path, exc))


def dump_yaml(data, path, logger=None):
    logger = logger or Logging.get_logger()

    real_path = normalize_path(path, logger=logger, fine_if_missing=True)

    try:
        with open(real_path, 'w') as f:
            YAML.dump(data, f)
            f.flush()

    except ruamel.yaml.YAMLError as exc:
        raise Exception("Unable to save YAML file '{}': {}".format(path, exc))


class Unit(object):
    def __init__(self, symbol):
        self.symbol = symbol

        self.aliases = [symbol]

        self.raising = None
        self.lowering = None

    @property
    def can_be_lowered(self):
        return self.lowering is not None

    @property
    def can_be_raised(self):
        return self.raising is not None

    def lower(self, amount):
        assert self.can_be_lowered

        lower_unit, k = self.lowering

        return Amount(amount * k, lower_unit)

    def raise_(self, amount):
        assert self.can_be_raised

        upper_unit, k = self.raising

        return Amount(amount * k, upper_unit)


class Amount(object):
    def __init__(self, amount, unit):
        self.amount = amount
        self.unit = unit

    @property
    def can_be_lowered(self):
        return self.unit.can_be_lowered

    @property
    def can_be_raised(self):
        return self.unit.can_be_raised

    def lower(self):
        return self.unit.lower(self.amount)

    def raise_(self):
        return self.unit.raise_(self.amount)

    def __repr__(self):
        return '<{} {}>'.format(self.amount, self.unit.symbol)


def load_units():
    unit_defs = load_yaml('units.yml')

    for symbol, properties in unit_defs.iteritems():
        unit = Unit(symbol)

        unit.aliases += properties.get('aliases', [])
        unit.raising = properties.get('raise', None)
        unit.lowering = properties.get('lower', None)

        for alias in unit.aliases:
            UNITS[alias] = unit

    for symbol, unit in UNITS.iteritems():
        if unit.raising is not None:
            unit.raising = (UNITS[unit.raising['unit']], unit.raising['C'])

        if unit.lowering is not None:
            unit.lowering = (UNITS[unit.lowering['unit']], unit.lowering['C'])
