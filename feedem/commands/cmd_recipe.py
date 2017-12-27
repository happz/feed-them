import click
import jinja2
import mdv

from ..db import Recipe
from . import cli


RECIPE_TEMPLATE = u"""
# {{ RECIPE['title'] }}

---

  * Complexity **{{ RECIPE['complexity'] }}**.
  * Ready in **{{ RECIPE.preparation_time }}** minutes.
  * Serves **{{ RECIPE['portions'] }}**.
  {% if RECIPE['tags'] %}
  * Tagged as {{ RECIPE['.pre-formatted']['tags'] | join(', ') }}
  {% endif %}

---

### Ingredients

{% for ingredient in RECIPE['ingredients'] %}
  {% if 'amount' in ingredient %}
  * {{ ingredient['name'] }}, {{ ingredient['amount'] }} {{ ingredient['unit'] }}
  {% else %}
  * {{ ingredient['name'] }}
  {% endif %}
{% endfor %}

---

### Steps

{% for step in RECIPE['steps'] %}
  {{ loop.index }}. {{ '**({:2d} minutes)**'.format(step['time']) if 'time' in step else '' }} {{ step['task'] }}
{% endfor %}
"""

mdv.term_columns = click.get_terminal_size()[0]


@cli.command(name='recipe', help='Display various aspects of a recipe.')
@click.argument('recipe_name', required=False)
@click.option('--recipe-id', default=None)
@click.option('--action', default='show', type=click.Choice(['show']))
@click.option('--scale', default=None)
@click.pass_context
def cmd_recipe(ctx, recipe_name, recipe_id, action, scale):
    logger = ctx.obj.logger

    if recipe_name is None and recipe_id is None:
        logger.error('Either pass recipe name, or use --recipe-id option.')
        return

    db = ctx.obj.open_database()

    recipe = Recipe.find(db, name=recipe_name, did=recipe_id)

    if not recipe:
        logger.error('No such recipe found.')
        return

    # adjust scaling
    if scale is not None:
        scales = {
            'adults': 0.0,
            'kids': 0.0
        }

        for bit in [s.strip() for s in scale.split(',')]:
            name, value = [s.strip() for s in bit.split('=')]

            scales[name] = float(value)
    else:
        scales = {
            'adults': recipe['portions'],
            'kids': 0.0
        }

    recipe.scale(scales)

    if action == 'show':
        recipe['.pre-formatted'] = {
            'tags': [u'**{}**'.format(tag) for tag in recipe['tags']]
        }

        text = jinja2.Template(RECIPE_TEMPLATE).render(RECIPE=recipe, SCALE=scales)

        formatted = mdv.main(text, theme='785.6556')

        click.echo(formatted)
