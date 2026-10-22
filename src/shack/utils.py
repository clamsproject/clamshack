"""

Assorted utilities for the core code and the cli code.

"""

# TODO: should be refactored a bit since it makes no sens that the commands and the
# messages are in here.


import os
import pathlib

from datetime import datetime
from rich import box, console, prompt, print
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.tree import Tree
from rich.filesize import decimal
from rich.markup import escape


# The record=True option is needed for the tests to work
console = console.Console(record=True)


def get_tree(directory, prefix=pathlib.Path('.'), full=False) -> Tree:
    """Get a rich.Tree instance starting at the given directory. Adapted from
    https://github.com/Textualize/rich/blob/main/examples/tree.py."""
    root = pathlib.Path(*directory.parts[len(prefix.parts):])
    root = path_as_string(root)
    root = root if root else "."
    tree = Tree(
        f":open_file_folder: [link file://{directory}]{root}",
        style="bold bright_blue", guide_style="bold bright_blue")
    walk_directory(pathlib.Path(directory), tree, full)
    return tree


def walk_directory(directory: pathlib.Path, tree: Tree, full) -> None:
    """Recursively build a Tree with directory contents. Adapted from
    https://github.com/Textualize/rich/blob/main/examples/tree.py."""
    paths = sorted(
        pathlib.Path(directory).iterdir(),
        key=lambda path: (path.is_file(), path.name.lower()))
    for path in paths:
        # Remove hidden files
        if path.name.startswith("."):
            continue
        if not full and path.suffix == ".mmif":
            continue
        if path.is_dir():
            style = "dim" if path.name.startswith("__") else ""
            branch = tree.add(
                f"[bold magenta]:open_file_folder: [link file://{path}]{escape(path.name)}",
                style=style,
                guide_style=style)
            walk_directory(path, branch, full)
        else:
            text_filename = Text(path.name, "green")
            text_filename.highlight_regex(r"\..*$", "bold red")
            text_filename.stylize(f"link file://{path}")
            file_size = path.stat().st_size
            text_filename.append(f" ({decimal(file_size)})", "blue")
            icon = "🐍 " if path.suffix == ".py" else "📄 "
            tree.add(Text(icon) + text_filename)


def log(fun):
    def wrapper(*args, **kwargs):
        print(fun.__name__, str(shack))
        return fun(*args, **kwargs)
    return wrapper


def info(text: str):
    message('INFO', 'bold dark_green', text)


def warning(text: str):
    message('WARNING', 'bold', text + '\n')
    #message('WARNING', 'bold dark_orange', text)


def error(text: str):
    message('ERROR', 'bold dark_red', text + '\n')


def message(message_type: str, style: str, text:str):
    console.print(Panel(Text(message_type, style)))
    console.print(f' {text}')


def dribble(text: str):
    console.print(text)


def bold(text: str) -> str:
    return f'\033[1m{text}\033[0m'


def timestamp() -> str:
    now = datetime.now()
    return now.strftime('%Y-%m-%dT%H:%M:%S')


def path_as_string(p: pathlib.Path) -> str:
    """Return a string for the directory path in the MMIF storage. It abbreviates
    the hash value of the parameters for clarity."""
    path_string = ''
    for triple in path_as_tuples(p):
        if len(triple) == 3:
            app, version, hash_value = triple
            if hash_value.endswith('.json'):
                path_string += f'{app}/{version}/{hash_value[:8]}.json'
            else:
                path_string += f'{app}/{version}/{hash_value[:8]}/'
        else:
            path_string += '/'.join([p for p in triple])
    return path_string if path_string else '~'


def path_as_tuples(p: pathlib.Path) -> list[tuple]:
    """Return the path a a list of tuples <appname, appversion, paramhash>. The
    last element in the list is not necessarily a tuple of lenth 3, it could also
    be <appname, appversion> or <appname>."""
    parts = p.parts
    return [parts[i:i + 3] for i in range(0, len(parts), 3)]


class FileSystemNode:

    """Abstract class which provides some intialization, sorting and other common
    functionality for path-like classes from the annotation and evaluation modules.

    name  --  the name of the directory or file
    path  --  the path of the node on the local working directory of the repository

    """

    # Note. This was originally taken from the annotation utilities in the dashboard
    # repository (internal-anno-eval-dashboard).


    def __init__(self, path: pathlib.Path):
        self.name = path.name
        self.path = path

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    def __str__(self):
        return f'<{self.__class__.__name__} {self.name}>'

