import click

from . import cli, cmd_edit_document
from ..db import Recipe


@cli.command(name='edit-recipe', help='Edit recipe.')
@click.argument('recipe_name', required=False)
@click.option('--recipe-id', default=None)
@click.pass_context
def cmd_edit_recipe(ctx, recipe_name, recipe_id):
    db = ctx.obj.open_database()

    if recipe_name is None and recipe_id is None:
        ctx.obj.logger.error('Either pass recipe name, or use --recipe-id option.')
        return

    recipe = Recipe.find(db, name=recipe_name, did=recipe_id)

    if not recipe:
        ctx.obj.logger.error('No such recipe found.')
        return

    cmd_edit_document(ctx, recipe, Recipe.validate)
