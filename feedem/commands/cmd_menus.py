import click
import tabulate

from . import cli
from ..db import Menu


def menu_list_view(db, menu_ids, *filters):
    for menu_id in menu_ids:
        menu = Menu.get(db, menu_id)

        if filters and not any(fn(menu) for fn in filters):
            continue

        yield menu_id, menu


@cli.command(name='menus')
@click.option('--tag', help='List only menus with this tag')
@click.pass_context
def cmd_menus(ctx, tag=None):
    db = ctx.obj.open_database()

    headers = [
        click.style(s, fg='red') for s in ['', 'Title', '', '', 'Tags', 'ID']
    ]

    table = []

    filters = []
    count = 0

    if tag is not None:
        filters.append(lambda menu: tag in menu['tags'])

    for menu_id, menu in menu_list_view(db, db.index['menus'], *filters):
        count += 1
        table.append([
            u'',
            menu['title'],
            '',
            '',
            u'\n'.join([u'- {}'.format(t) for t in menu['tags']]),
            click.style(menu_id, fg='blue')
        ])

    click.echo(tabulate.tabulate(table, headers, tablefmt="simple"))

    click.secho('')
    click.secho('{} menus'.format(count), fg='green')
