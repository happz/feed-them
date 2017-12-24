import click

from . import cli, cmd_edit_document
from ..db import Recipe


@cli.command(name='edit-recipe')
@click.option('--recipe-id', required=True)
@click.pass_context
def cmd_edit_recipe(ctx, recipe_id):
    db = ctx.obj.open_database()

    cmd_edit_document(ctx, Recipe.get(db, recipe_id), Recipe.validate)
