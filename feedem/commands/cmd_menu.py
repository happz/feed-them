import collections

import click
import jinja2
import mdv

from ..db import Menu, Recipe
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
    {% set real_recipe = Recipe.find(DB, name=recipe, did=recipe) %}
    {% if not real_recipe %}
    * {{ recipe }} [Cannot find the recipe]
    {% else %}
    * {{ recipe }}
    {% endif %}
  {% endfor %}

{% endfor %}

{% endfor %}
"""

SHOPPING_LIST_TEMPLATE = u"""
# {{ MENU['title'] }}

---

{% for name, amounts in SHOPPING_LIST.iteritems() %}
#### {{ name }}

  {% for amount in amounts %}
    {% if amount %}
  * {{ amount.amount }} {{ amount.unit.symbol }}
    {% endif %}
  {% endfor %}
{% endfor %}
"""

mdv.term_columns = click.get_terminal_size()[0]


@cli.command(name='menu', help='Display various aspects of a menu.')
@click.argument('menu_name', required=False)
@click.option('--menu-id')
@click.option('--action', default='show', type=click.Choice(['show', 'shopping-list']))
@click.option('--scale', default=None)
@click.pass_context
def cmd_menu(ctx, menu_name, menu_id, action, scale):
    db = ctx.obj.open_database()
    logger = ctx.obj.logger

    if menu_name is None and menu_id is None:
        logger.error('Either pass menu name, or use --menu-id option.')
        return

    menu = Menu.find(db, name=menu_name, did=menu_id)

    if not menu:
        logger.error('No such menu found')
        return

    if action == 'show':
        menu['.pre-formatted'] = {
            'tags': [u'**{}**'.format(tag) for tag in menu['tags']]
        }

        text = jinja2.Template(MENU_TEMPLATE).render(DB=db, MENU=menu, Recipe=Recipe)

        formatted = mdv.main(text, theme='785.6556')

        click.echo(formatted)

    elif action == 'shopping-list':
        shopping_list = collections.defaultdict(list)

        for day in menu['schedule']:
            for meal in day['meals']:
                for recipe_name in meal['recipes']:
                    recipe = Recipe.find(db, name=recipe_name, did=recipe_name)

                    if not recipe:
                        logger.warn("Cannot find recipe '{}'".format(recipe_name))
                        continue

                    recipe.scale(menu['guests'])

                    for ingredient in recipe['ingredients']:
                        if 'amount' in ingredient:
                            shopping_list[ingredient['name']].append(ingredient['amount'])

                        else:
                            shopping_list[ingredient['name']].append(None)

        text = jinja2.Template(SHOPPING_LIST_TEMPLATE).render(MENU=menu, SHOPPING_LIST=shopping_list)
        formatted = mdv.main(text, theme='785.6556')
        click.echo(formatted)
