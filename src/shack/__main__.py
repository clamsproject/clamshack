import sys
import json
import urllib
from pathlib import Path

from mmif.utils.workflow_helper import generate_workflow_identifier
from shack import ClamShack, batch, annotations, evaluations


def print_batches(repo, n=3):
    print()
    for n in range(n):
        print(repo.batches[n])


def print_projects(repo):
    print()
    for n in range(len(repo.projects)):
        print(f'{repo.projects[n]}')


def print_entity_experiments(repo):
    neproj = repo.get_project('newshour-namedentity')
    print(f'\n{neproj}')
    first_gold = neproj.golds[0]
    print('BLOB', first_gold, first_gold.name)
    print(first_gold.content[:200])
    drop = neproj.get_drop('220601-aapb-collaboration-21')
    print(drop)
    print(drop.file_names[:3])
    print(drop.file_content(drop.file_names[0])[:200])


def print_swt_experiments(shack, repo):
    shack.cd('swt-detection/v8.6/d41d8cd98f00b204e9800998ecf8427e')
    files = shack.files()
    identifiers = [p.stem for p in files]
    # throw in some that are annotated
    identifiers.extend(['cpb-aacip-0009a7e5474', 'cpb-aacip-00a9ed7f2ba'])
    swtproj = repo.get_project('scene-recognition')
    drop = swtproj._drops['240814-aapb-collaboration-27-e']
    print(f'\n{drop}')
    for identifier in identifiers:
        present = '+' if identifier in swtproj.gold_names else '-'
        data_drop = ''
        if present == '+':
            for drop in swtproj.drops:
                if identifier in drop:
                    data_drop = drop.name
                    break
        print(f'{present} {identifier} {data_drop}')


class ShackBuilder:

    """Class to help build a shack from a directory of MMIF files."""

    # TODO: 
    # - Maybe refactor the code in core.ClamShack to have a more versatile
    #   process of building shacks and obviating the need for this.
    # - The created assets list is not perfect, this is not a problem as long
    #   as the shack created does not need access to the assets.
    # - This is not very well tested and may only work for simple cases.

    def __init__(self, shackname):
        """Creates the minimal directory structure for a shack."""
        self.location = Path(shackname)
        self.document_locations = set()
        for subdir in ('mmif', 'assets', 'sources', 'jobs'):
            (self.location / subdir).mkdir(parents=True)
        print(f'\nCreated proto shack at "{shackname}"')

    def add_mmif_files(self, mmif_directory, max_files):
        """Adds MMIF files from a directory. Walk through the directory looking
        for MMIF files, create MMIF sources from the MMIF files, add the sources
        and MMIF files to the shack and create a list of assets from the location
        values."""
        print(f'Using MMIF files from "{mmif_directory}"')
        for root, dirs, _files in Path(mmif_directory).walk():
            for d in dirs:
                count = 0
                for mmif_file in (root / d).iterdir():
                    if not mmif_file.suffix == '.mmif':
                        continue
                    count += 1
                    if count > max_files:
                        break
                    self.add_mmif_file(mmif_file)
        self.create_assets_list_from_locations()

    def add_mmif_file(self, mmif_file: Path):
        print(mmif_file)
        with open(mmif_file, 'r') as fh:
            data = json.load(fh)
            for doc in data['documents']:
                self.document_locations.add(doc['properties']['location'])
            params = data['views'][0]['metadata'].get('parameters',{})
            wfid = generate_workflow_identifier(mmif_file)
            wfid_dir = self.location / 'mmif' / wfid 
            wfid_dir.mkdir(parents=True, exist_ok=True)
            mfile = wfid_dir / mmif_file.name
            pfile = self.location / 'mmif' / f'{wfid}.json'
            sfile = self.location / 'sources' / mmif_file.name
            mfile.write_text(json.dumps(data, indent=2))
            pfile.write_text(json.dumps(params, indent=2))
            data['views'] = []
            sfile.write_text(json.dumps(data, indent=2))

    def create_assets_list_from_locations(self):
        """Create an asset list from the locations in a rather simplistic way that
        only deals with the few cases I looked at."""
        assets_head = '/'
        assets = set()
        for loc in self.document_locations:
            split = urllib.parse.urlsplit(loc)
            if split.scheme:
                assets_head = f'{split.scheme}://'
            assets.add(Path(loc).name)
        with open(self.location / 'assets' / 'list.txt', 'w') as fh:
            fh.write(f'{assets_head}\n\n')
            for a in sorted(assets):
                fh.write(f'{a}\n')


if sys.argv[1] == 'batch':
    sys.argv.pop(1)
    args = batch.arg_parser().parse_args()
    batch.main(args)

elif sys.argv[1] == 'anno':
    # experimenting with the repository code
    shack = ClamShack(sys.argv[2], None)
    repo = annotations.AnnotationRepository(sys.argv[3])
    print(f'\n{repo}')
    #print_batches(repo)
    #print_projects(repo)
    #print_entity_experiments(repo)
    print_swt_experiments(shack, repo)

elif sys.argv[1] == 'eval':
    # experimenting with the repository code
    shack = ClamShack(sys.argv[2], None)
    repo = evaluations.EvaluationRepository(sys.argv[3])
    print(f'\n{repo}')
    #print_batches(repo)
    #print_projects(repo)
    #print_entity_experiments(repo)
    #print_swt_experiments(shack, repo)

elif sys.argv[1] == 'create':
    builder = ShackBuilder(sys.argv[2])
    builder.add_mmif_files(sys.argv[3], int(sys.argv[4]))
