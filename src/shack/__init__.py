"""

Does some imports for easy access and defines the functionality that is linked
to the shack project script.

"""

import pathlib
import importlib
import shutil
import argparse

import mmif_storage

from shack.core import ClamShack, ShackError
from shack.core import History, Assets, StoragePath, MmifIndex, Job
from shack.cli import Shell


def start_shack():
    args = parse_shack_arguments()
    Shell(ClamShack(args.dir, args.assets)).cmdloop()


def create_shack_example():
    # TODO: with this example, running "dir -s" gives an error
    args = parse_create_shack_arguments()
    directory = pathlib.Path(args.dir)
    if directory.exists():
        return f'Directory {args.dir} allready exists, not creating example'
    mmif_storage.create_storage_example(directory / 'mmif')
    for subdir in ('assets', 'jobs', 'sources'):
        (directory / subdir).mkdir()
    spacy_path = (
        directory / 'mmif' /'swt-detection/v8.6/d41d8cd98f00b204e9800998ecf8427e' 
        / 'smolvlm2-captioner/v1.0/d41d8cd98f00b204e9800998ecf8427e' / 'spacy-wrapper')
    shutil.rmtree(spacy_path)
    data_path = importlib.resources.files() / 'data'
    shutil.copyfile(data_path / 'assets.txt', directory / 'assets' / 'list.txt')
    shutil.copy(data_path / 'j1-swt.txt', directory / 'jobs')
    shutil.copy(data_path / 'j2-captioner.txt', directory / 'jobs')
    for n in (1,2):
        # TODO: the location in these files may have to change
        fname = f'cpb-aacip-f551104e446-clip{n}.mmif'
        shutil.copy(data_path / fname, directory / 'sources')


def parse_shack_arguments():
    parser = argparse.ArgumentParser(description="Open or create a ClamShack")
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


def parse_create_shack_arguments():
    parser = argparse.ArgumentParser(description="Create an example ClamShack")
    parser.add_argument(
        'dir', nargs='?', metavar='DIRECTORY', default='example-shack',
        help='directory to create the shack in, default is "example-shack"')
    return parser.parse_args()
