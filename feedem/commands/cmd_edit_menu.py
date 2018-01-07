import click

from . import cli, cmd_edit_document
from ..db import Menu


@cli.command(name='edit-menu', help='Edit menu.')
@click.argument('menu_name', required=False)
@click.option('--menu-id')
@click.pass_context
def cmd_edit_menu(ctx, menu_name, menu_id):
    db = ctx.obj.open_database()
    logger = ctx.obj.logger

    if menu_name is None and menu_id is None:
        logger.error('Either pass menu name, or use --menu-id option.')
        return

    menu = Menu.find(db, name=menu_name, did=menu_id)

    if not menu:
        logger.error('No such menu found')
        return

    cmd_edit_document(ctx, menu, Menu.validate)
