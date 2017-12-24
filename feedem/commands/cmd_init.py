import os.path

import click

from ..db import DB

from . import cli


@cli.command(name='init')
@click.pass_context
def cmd_init(ctx):
    if os.path.exists(ctx.obj.database_path):
        click.confirm('Database already exists at {}. Do you want to re-initialize it?', abort=True)

    logger = ctx.obj.logger

    logger.info('Initializing database at {} ...'.format(ctx.obj.database_path))

    DB.initialize(ctx.obj.database_path)

    logger.info('Done.')
