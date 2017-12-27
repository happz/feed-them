import click

from . import cli, cmd_new_document
from ..db import Recipe


@cli.command(name='new-recipe', help='Create a new recipe.')
@click.pass_context
def cmd_new_recipe(ctx):
    template = u"""---

# Human-readable name of the recipe, e.g. "Sunkofleky" or "Burtgulas".
title:


# Number of people served. Count with common adults, no kids.
portions:


# List of tags, e.g. "kid-friendly", "easy", "breakfast" or "luch"

tags:
# - foo
# - bar


# On scale 1 to 10, with 1 being the easiest
complexity:


# List of extra tools and instruments required. It probably makes no sense to mention a knife
# but it might be a good idea to list things like "owen", "1 small pan, 1 large pan" or "yogurt maker".
equipment:
# - foo
# - bar


# List of ingredients. Each is described by following fields:
#
# - "name" - human-readable name of the ingredient, e.g. "onion", "duck" or "whole cow";
# - "amount" - how many onions, how much sugar, how many cows? Omit a unit, just the number;

ingredients:
  - name: foo
    amount: 100 g


# List of steps. Each step is described by several fields:
#
# - "task" descibes what's needs to be done - peel the onions, chop the celery, bake the damn cake. Be
#   verbose when necessary, you're writing a recipe.
#
# - "time" to finish this step. 1 minute to peel two onions, or 300 minutes to slowly roast the duck.

steps:
  - task: foo
    time: 60


# Comments and notes - just list them.

comments:
#  - foo
"""

    cmd_new_document(ctx, 'recipes', template, Recipe)
