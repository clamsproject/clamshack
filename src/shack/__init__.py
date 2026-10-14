"""

Does some imports for easy access and defines the functionality that is linked
to the shack project script.

"""

import argparse

from shack.core import ClamShack, ShackError
from shack.core import History, Assets, MmifIndex, Job
from shack.cli import Shell
from shack.run import ClamsApp


def start_shack():
    args = parse_arguments()
    Shell(ClamShack(args.dir, args.assets)).cmdloop()


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--dir',
        metavar='DIR', default='.',
        help=("Open the ClamShack in DIR or create it if the directory does not "
              "\nexist. If the directory does not exist then the --assets argument "
              "\nbecomes required."))
    parser.add_argument(
        '--assets',
        metavar='FILE', default=None,
        help="Use the assets in FILE when creating a new ClamShack in DIR.")
    return parser.parse_args()
