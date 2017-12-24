import os.path
import ruamel.yaml

from .log import Logging, log_dict


YAML = ruamel.yaml.YAML()
YAML.indent(sequence=4, mapping=4, offset=2)


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


def lower_unit(unit, amount):
    unit_sequences = (
        # weight
        (
            (None, 'g'),
            (10.0, 'dkg'),
            (100.0, 'kg')
        ),
        # volume
        (
            (None, 'ml'),
            (100.0, 'dl'),
            (10.0, 'l')
        )
    )

    logger = Logging.get_logger()

    logger.debug('unit={}, amount={}'.format(unit, amount))

    for unit_sequence in unit_sequences:
        if not any([unit in step for step in unit_sequence]):
            continue

        logger.debug('unit sequence {}'.format(unit_sequence))

        for i, (treshold, next_unit) in enumerate(unit_sequence):
            if next_unit != unit:
                continue
            break

        for treshold, next_unit in unit_sequence[i + 1:]:
            logger.debug('step {}, {}'.format(treshold, next_unit))

            if amount < treshold:
                logger.debug('lowered to {} {}'.format(amount, unit))
                return unit, amount

            amount /= treshold
            unit = next_unit

        logger.debug('lowered to {} {}'.format(amount, unit))
        return unit, amount

    else:
        logger.debug('no unit sequence found')
        return unit, amount
