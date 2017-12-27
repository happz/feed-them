import click

from . import cli, cmd_new_document
from ..db import Menu


@cli.command(name='new-menu', help='Create a new menu.')
@click.pass_context
def cmd_new_menu(ctx):
    template = u"""---

# Human-readable name of the menu, e.g. "Tabor 2018" or "Vikend na chalupe".
title:


# Number of people served.
guests:
  adults:
  kids:


# List of tags, e.g. "tabor" or "chalupa".

tags:
#   - tag #1
#   - tag #2


# Comments and notes - just list them.

comments:
#    - foo


# Schedule

schedule:
  - name:  # Arbitrary name of the day, e.g. "pondeli", "prijezd" or "24. 7. - utery". Used as a label.

    # List of meals. Order matters - if you put breakfast after lunch, shopping lists may not be correct.
    meals:
      - name:    # Name of the meal, e.g. "snidane", "odpoledni svacina" or "balicek na vylet"
        recipes: # List of recipe IDs
          - foo
          - bar
"""

    cmd_new_document(ctx, 'menus', template, Menu)
