import os.path
import sys
import tempfile
import uuid

import click

from .. import normalize_path, load_yaml
from ..db import DB
from ..log import Logging, ContextAdapter


class GlobalContext(object):
    logger = None
    database_path = None
    db = None

    def open_database(self):
        if not os.path.exists(self.database_path):
            self.logger.error('Database path {} does not exist. If the path is correct, please run `feed-em init` first.'.format(self.database_path))
            sys.exit(1)

        self.db = DB(self.database_path)
        return self.db


@click.group()
@click.option('--database-path', type=click.Path(exists=False, file_okay=False, writable=True), envvar='FEEDEM_DATABASE_PATH', default='~/.feed-em')
@click.pass_context
def cli(ctx, database_path):
    ctx.obj = obj = GlobalContext()

    obj.logger = Logging.create_logger()
    obj.logger = ContextAdapter(obj.logger)

    obj.database_path = normalize_path(database_path, fine_if_missing=True)


def edit_yaml(text, validator):
    logger = Logging.get_logger()

    f = tempfile.NamedTemporaryFile(suffix='.yml', delete=False)
    f.close()

    with click.open_file(f.name, mode='w', encoding='utf-8') as f:
        f.write(text)
        f.flush()

    while True:
        click.edit(filename=f.name)

        try:
            data = load_yaml(f.name)

        except Exception:
            validation_result = 'it is broken'

        else:
            validation_result = validator(data)

            if validation_result is not True:
                validation_result = 'item {} has invalid value: {}'.format('.'.join(validation_result.path), validation_result.message)

        if validation_result is not True:
            logger.error('Recipe is not valid, {}'.format(validation_result))

            if click.confirm('Found errors. Y to re-edit, N to drop changes') is not True:
                return None

            continue

        with click.open_file(f.name, mode='r', encoding='utf-8') as f:
            return f.read()


def cmd_edit_document(ctx, document, validator):
    logger = ctx.obj.logger
    ctx.obj.open_database()

    document_text = edit_yaml(document.raw, validator)

    if document_text is None:
        logger.info('Ack, no changes made')
        return

    document.raw = document_text
    logger.info('Ack, {} updated'.format(document.document_id))


def cmd_new_document(ctx, document_type, template, document_class):
    logger = ctx.obj.logger
    db = ctx.obj.open_database()

    document_text = edit_yaml(template, document_class.validate)

    if document_text is None:
        logger.info('Ack, no document created')
        return

    document_id = uuid.uuid4().hex
    logger.info('New ID is {}'.format(document_id))

    document = document_class.new(db, document_id)
    document.raw = document_text

    index = db.index
    index[document_type].append(document_id)
    index.save(force=True)
