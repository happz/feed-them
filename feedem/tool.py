from .commands import cli  # noqa
from .commands.cmd_edit_recipe import cmd_edit_recipe  # noqa
from .commands.cmd_init import cmd_init  # noqa
from .commands.cmd_menu import cmd_menu  # noqa
from .commands.cmd_menus import cmd_menus  # noqa
from .commands.cmd_new_menu import cmd_new_menu  # noqa
from .commands.cmd_new_recipe import cmd_new_recipe  # noqa
from .commands.cmd_recipe import cmd_recipe  # noqa
from .commands.cmd_recipes import cmd_recipes  # noqa


if __name__ == '__main__':
    cli()
