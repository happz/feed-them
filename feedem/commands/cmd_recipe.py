import click
import jinja2
import mdv

from .. import lower_unit
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
  {{ loop.index }}. {{ '**({} minutes)**'.format(step['time']) if 'time' in step else '' }} {{ step['task'] }}
{% endfor %}
"""

mdv.term_columns = click.get_terminal_size()[0]


@cli.command(name='recipe')
@click.option('--recipe-id', required=True)
@click.option('--action', default='show', type=click.Choice(['show']))
@click.option('--scale', default=None)
@click.pass_context
def cmd_recipe(ctx, recipe_id, action, scale):
    db = ctx.obj.open_database()

    recipe = db.get_recipe(recipe_id)

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

    for ingredient in recipe['ingredients']:
        if 'amount' not in ingredient:
            continue

        splitted = ingredient['amount'].split(' ')

        amount = float(splitted[0])
        unit = splitted[-1]

        # scale amount
        amount = amount / recipe['portions'] * scales['adults']

        # lower units
        unit, amount = lower_unit(unit, amount)

        ingredient['amount'] = amount
        ingredient['unit'] = unit

    if action == 'show':
        recipe['.pre-formatted'] = {
            'tags': [u'**{}**'.format(tag) for tag in recipe['tags']]
        }

        text = jinja2.Template(RECIPE_TEMPLATE).render(RECIPE=recipe, SCALE=scales)

        formatted = mdv.main(text, theme='785.6556')

        click.echo(formatted)
