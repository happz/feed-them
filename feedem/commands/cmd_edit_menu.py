import click

from . import cli, cmd_edit_document
from ..db import Menu


@cli.command(name='edit-menu', help='Edit menu.')
@click.option('--menu-id', required=True)
@click.pass_context
def cmd_edit_menu(ctx, menu_id):
    db = ctx.obj.open_database()

    cmd_edit_document(ctx, Menu.get_document(db, menu_id), Menu.validate)
