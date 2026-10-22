import sys
from shack import ClamShack, batch, annotations


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


if sys.argv[1] == 'batch':
    sys.argv.pop(1)
    args = batch.arg_parser().parse_args()
    batch.main(args)


if sys.argv[1] == 'anno':
    # experimenting with the repository code
    shack = ClamShack(sys.argv[2], None)
    repo = annotations.Repository(sys.argv[3])
    print(f'\n{repo}')
    #print_batches(repo)
    #print_projects(repo)
    #print_entity_experiments(repo)
    print_swt_experiments(shack, repo)



'''
from shack.annotations import Repository
repo = Repository('../aapb/aapb-annotations')
identifier = 'cpb-aacip-00a9ed7f2ba'
swtproj = repo.get_project('scene-recognition')
drop = swtproj._drops['240814-aapb-collaboration-27-e']
print(drop)
print(drop.file_names)
'''
