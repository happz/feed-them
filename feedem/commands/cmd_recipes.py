import click
import tabulate

from . import cli
from ..db import Recipe


def recipe_list_view(db, recipe_ids, *filters):
    for recipe_id in recipe_ids:
        recipe = Recipe.get(db, recipe_id)

        if filters and not any(fn(recipe) for fn in filters):
            continue

        yield recipe_id, recipe


@cli.command(name='recipes')
@click.option('--tag', help='List only recipes with this tag')
@click.pass_context
def cmd_recipes(ctx, tag=None):
    db = ctx.obj.open_database()

    headers = [
        click.style(s, fg='red') for s in ['', 'Title', 'Portions', 'Time (minutes)', 'Tags', 'ID']
    ]

    table = []

    filters = []
    count = 0

    if tag is not None:
        filters.append(lambda recipe: tag in recipe['tags'])

    for recipe_id, recipe in recipe_list_view(db, db.index['recipes'], *filters):
        count += 1
        table.append([
            u'',
            recipe['title'],
            recipe['portions'],
            sum([step.get('time', 0) for step in recipe.data['steps']]),
            u'\n'.join([u'- {}'.format(t) for t in recipe['tags']]),
            click.style(recipe_id, fg='blue')
        ])

    click.echo(tabulate.tabulate(table, headers, tablefmt="simple"))

    click.secho('')
    click.secho('{} recipes'.format(count), fg='green')
