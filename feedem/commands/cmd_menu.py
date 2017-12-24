import click
import jinja2
import mdv

from ..db import Menu
from . import cli


MENU_TEMPLATE = u"""
# {{ MENU['title'] }}

---

  {% if MENU['tags'] %}
  * Tagged as {{ MENU['.pre-formatted']['tags'] | join(', ') }}
  {% endif %}

---

### Guests

  * **{{ MENU['guests']['adults'] }}** adults
  * **{{ MENU['guests']['kids'] }}** kids

---

## Schedule

{% for day in MENU['schedule'] %}

### {{ day['name'] }}

{% for meal in day['meals'] %}

 * **{{ meal['name'] }}**:
  {% for recipe in meal['recipes'] %}
    * {{ recipe }}
  {% endfor %}

{% endfor %}

{% endfor %}
"""

mdv.term_columns = click.get_terminal_size()[0]


@cli.command(name='menu')
@click.option('--menu-id', required=True)
@click.option('--action', default='show', type=click.Choice(['show']))
@click.option('--scale', default=None)
@click.pass_context
def cmd_menu(ctx, menu_id, action, scale):
    db = ctx.obj.open_database()

    menu = Menu.get(db, menu_id)

    if action == 'show':
        menu['.pre-formatted'] = {
            'tags': [u'**{}**'.format(tag) for tag in menu['tags']]
        }

        text = jinja2.Template(MENU_TEMPLATE).render(MENU=menu)

        formatted = mdv.main(text, theme='785.6556')

        click.echo(formatted)
